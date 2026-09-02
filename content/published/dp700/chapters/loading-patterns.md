# Design and implement loading patterns

<!-- block-id: orientation -->
A loading pattern is a correctness contract, not merely a transfer method. Define how records are selected, keyed, validated, applied, retried, and reconciled before choosing the Fabric activity.

## Objective coverage

| Measured objective | What to master |
| --- | --- |
| Design and implement full and incremental data loads | Snapshots, watermarks, CDC, upserts, deletes, idempotency, and reconciliation |
| Prepare data for loading into a dimensional model | Grain, surrogate keys, dimensions, facts, SCD behavior, and late members |
| Design and implement a loading pattern for streaming data | Event time, checkpoints, deduplication, windows, late data, and serving layers |

## Design and implement full and incremental data loads

A **full load** replaces or rebuilds the target from the complete selected source. It is simple and self-reconciling but can be expensive and disruptive. An **incremental load** selects only changes since a trusted position, reducing work while increasing state-management complexity.

| Change signal | Strength | Main risk |
| --- | --- | --- |
| Monotonic ID | Simple | Updates and deletes may be invisible |
| Modified timestamp | Widely available | Clock precision, ties, and late commits |
| Source CDC/version | Captures inserts, updates, and often deletes | Retention and ordering must be managed |
| File/path partition | Efficient for append-oriented sources | Rewritten or late partitions need reconciliation |

Persist a **high-water mark** only after the target transaction or durable write succeeds. Read an overlap window when timestamps can collide or arrive late, then deduplicate by business key and source version. A safe retry either overwrites a deterministic partition or performs an idempotent upsert.

```sql
MERGE dbo.Customer AS target
USING #CustomerStage AS source
ON target.CustomerBusinessKey = source.CustomerBusinessKey
WHEN MATCHED AND source.ModifiedAt > target.ModifiedAt THEN
  UPDATE SET CustomerName = source.CustomerName,
             ModifiedAt = source.ModifiedAt
WHEN NOT MATCHED THEN
  INSERT (CustomerBusinessKey, CustomerName, ModifiedAt)
  VALUES (source.CustomerBusinessKey, source.CustomerName, source.ModifiedAt);
```

`MERGE` is not automatically correct: the staged source must contain at most one winning row per target key, delete semantics must be explicit, and concurrency must be tested. Periodic full or bounded reconciliation detects changes missed by the incremental signal.

## Prepare data for loading into a dimensional model

Declare a fact table's **grain** in one sentence before selecting columns—for example, “one row per order line at posting time.” Every fact and dimension key must agree with that grain.

Dimensions describe business entities and normally use warehouse surrogate keys. Facts store measurements and foreign keys to dimensions. Load dimensions before facts so natural/business keys can be resolved to surrogate keys.

| Dimension change | Behavior | Use when |
| --- | --- | --- |
| Type 1 | Overwrite current value | History is unneeded or correction is intended |
| Type 2 | Expire old row and insert a new version | Reports must reproduce historical attributes |

A Type 2 row commonly has `ValidFrom`, `ValidTo`, and `IsCurrent`. Detect a change in tracked attributes, expire the current record, and insert a new surrogate-keyed version. Facts resolve the version valid at the event's business time.

Late-arriving dimensions require an **unknown/inferred member** rather than rejecting every fact. Load the fact against that stable surrogate key, then update or restate according to the chosen policy when the dimension arrives. Degenerate dimensions such as order number can remain on the fact when they have no useful descriptive dimension row.

Validate uniqueness of dimension business keys, referential integrity, fact counts, additive behavior, and totals against a trusted control. A star schema is not merely denormalization; it is a deliberate grain-and-relationship model for analytics.

## Design and implement a loading pattern for streaming data

Streaming replaces a single batch boundary with continuously advancing state. Distinguish **event time** (when the business event occurred) from **processing time** (when the engine handled it). Windowing and late-data policy normally use event time.

A reliable pattern is:

1. Ingest immutable events and retain source metadata.
2. Validate schema and quarantine malformed events.
3. Deduplicate using an event ID and bounded state.
4. Apply event-time windows and a watermark defining tolerated lateness.
5. Write to an idempotent sink with a durable checkpoint.
6. Serve curated tables and reconcile them from retained raw events.

“Exactly once” should be treated as an end-to-end property. A streaming engine checkpoint cannot prevent duplication if the source reuses IDs or the sink performs non-idempotent side effects. Choose the watermark from measured lateness: too short drops legitimate events; too long retains more state and delays final results.

## Full and incremental load field guide

<!-- block-id: full-incremental-model -->
Separate four decisions: **selection** chooses source changes, **transport** moves
them, **application** changes the target, and **control state** records progress.
A full load selects the complete scope and commonly replaces, truncates/reloads,
or swaps a rebuilt target. An incremental load selects a bounded change set and
applies inserts, updates, and possibly deletes. A pipeline, notebook, or SQL
procedure can participate in either pattern; the tool does not define the
semantics.

<!-- block-id: full-incremental-operations -->
For timestamp incrementals, read the last committed watermark `W0`, choose an
upper bound `W1` at run start, and extract `ModifiedAt > W0 AND ModifiedAt <=
W1`, usually with a justified overlap before `W0`. Land the extract with source
version and run ID, validate it, select one winning version per business key,
and apply it idempotently. Reconcile counts and control totals. Only after the
target commit succeeds, store `W1` as the new committed watermark. Preserve the
staged range until the run is recoverable.

<!-- block-id: full-incremental-decisions -->
Use a full load for small datasets, first loads, recovery, or sources without a
trustworthy change signal. Use CDC when inserts, updates, deletes, and ordering
must be captured. Use a timestamp or version watermark when it is stable and
indexed. Use partition discovery for append-oriented files, but include a late
partition policy. Incremental loading saves work at the cost of state, delete
handling, and reconciliation. Periodic bounded or full comparisons are the
safety net against silent gaps.

<!-- block-id: full-incremental-example -->
**Worked recovery.** The committed watermark is 10:00. A run chooses 10:15,
loads staging, merges the target, and crashes before saving control state. On
retry it reads the same interval, ranks duplicate staged rows by source version,
and performs the same keyed upsert; the result remains one current row per key.
If the watermark had advanced before the merge, the retry would begin after
10:15 and permanently miss the interval. This is why progress follows durable
target success.

<!-- block-id: full-incremental-diagnostics -->
For missing rows, inspect source change retention, extraction bounds, time-zone
conversion, precision ties, overlap, rejected rows, merge predicates, and when
the watermark advanced. For duplicates, inspect source-key uniqueness, winning
version logic, target constraints, and concurrent writers. For slow loads,
measure source scan, transfer, staging, target application, and validation
separately. Mini-lab: run the same increment twice, fail once before target
commit and once after target commit but before control update, and prove the
final target and watermark are correct in both cases.

## Dimensional loading field guide

<!-- block-id: dimensional-model -->
Dimensional loading preserves a declared analytical grain while translating
source business keys into warehouse surrogate keys. Dimensions supply durable
descriptive context; facts record events or measurements at the chosen grain.
A Type 1 change corrects or replaces current attributes. A Type 2 change creates
a new version so a historical fact can resolve the attributes valid at its
business time. The order is normally stage → validate → load dimensions →
resolve keys → load facts → reconcile.

<!-- block-id: dimensional-operations -->
Profile each dimension business key for nulls and duplicates. Insert a stable
unknown member. For Type 1, update changed tracked columns. For Type 2, compare
a normalized attribute hash or explicit columns; expire the current record and
insert a new surrogate-keyed row with nonoverlapping validity. Then join staged
facts to the dimension on business key and event time where history applies.
Reject or route facts that violate grain, and use the unknown/inferred member
for permitted late dimensions. Validate foreign keys and totals before publish.

<!-- block-id: dimensional-decisions -->
Use Type 1 for corrections or attributes whose history has no analytical value;
use Type 2 when reports must reproduce the past. Do not make every attribute
Type 2: it increases row count and fact-key lookup complexity. Choose an
accumulating snapshot for a process whose milestones update one logical row, a
periodic snapshot for measurements at regular periods, and a transaction fact
for individual events. A degenerate identifier belongs on the fact when it has
no useful dimension attributes.

<!-- block-id: dimensional-example -->
**Worked late member.** Order 501 arrives for customer `C42`, but the customer
dimension has no `C42`. The fact load uses surrogate key 0, the governed unknown
member, and records the unresolved business key. When `C42` arrives, the
dimension receives a real surrogate key. Policy determines whether the order is
restated to that key or remains unknown for the historical load. Silently
dropping the order would preserve referential cleanliness by destroying
completeness—an unacceptable trade.

<!-- block-id: dimensional-diagnostics -->
If fact totals multiply, verify the fact grain and dimension join is one winning
row per business key and event time. If a Type 2 dimension has two current rows,
inspect concurrent loads and enforce a serialized/keyed transition. If many
facts use the unknown key, alert on rate and age, then inspect dimension timing,
normalization, and source keys. Mini-lab: load one customer, change a Type 1
attribute and a Type 2 attribute, then load facts before and after the change;
write the expected surrogate keys and historical report output before running.

## Streaming load field guide

<!-- block-id: streaming-load-model -->
A durable streaming load usually has bronze, validated, and serving boundaries.
The raw/bronze layer preserves replayable events and source metadata. Stateful
processing uses event time, event identity, checkpoints, watermarks, and bounded
windows. The serving layer uses an idempotent Delta or Eventhouse write pattern.
Recovery correctness spans source replay plus processing state plus sink
semantics; no single “exactly once” checkbox proves the whole chain.

<!-- block-id: streaming-load-operations -->
Define schema, event ID, event-time column, expected lateness, source retention,
and replay ownership. Land raw events before lossy filtering when possible.
Validate and quarantine malformed records. Apply a watermark chosen from an
observed lateness distribution, deduplicate within a bounded horizon, and keep a
unique checkpoint for each query. Write stable keys or deterministic partitions
to the sink and record batch/offset information. Monitor input rate, processing
rate, lag, state size, late drops, bad events, and sink failures.

<!-- block-id: streaming-load-decisions -->
Use a short watermark only when the business accepts more late-event loss in
exchange for smaller state and earlier final output. Use `foreachBatch` when
micro-batches need existing batch logic, but key writes by batch ID or event
identity. Retain raw data long enough to replay beyond checkpoint corruption or
logic defects. A dead-letter stream preserves diagnosable bad input; it should
include reason, original payload reference, source position, and processing
version without leaking sensitive data into broad logs.

<!-- block-id: streaming-load-example -->
**Worked recovery.** A device event reaches bronze twice with one `event_id`.
The silver query uses a 30-minute watermark and deduplicates that ID, then
writes by deterministic key. After a checkpointed restart, the source replays a
range, but already committed progress and the idempotent sink prevent a second
logical output. An event arriving 45 minutes late is routed or counted according
to policy; the system does not pretend it never existed.

<!-- block-id: streaming-load-diagnostics -->
When lag grows, compare input and processing rates, micro-batch duration,
shuffle/state size, sink latency, and capacity. When counts drift, inspect event
IDs, watermark delay, late-drop metrics, checkpoint history, replay range, and
sink idempotency. Never delete a checkpoint merely to clear an error without a
replay plan. Mini-lab: process an on-time event, a duplicate, a late-within-
watermark event, a too-late event, and a malformed event; predict bronze,
silver, quarantine, and aggregate results before execution.

<!-- block-id: loading-exam-distinctions -->
Exam questions often mix similarly named state. A batch high-water mark bounds
source changes; an event-time watermark bounds streaming lateness and state; a
checkpoint stores streaming recovery progress. Surrogate keys are warehouse
identities; business keys come from source domains. Checkpoint recovery does not
repair non-idempotent side effects, and `MERGE` does not repair duplicate source
keys without a winning-row rule.

<!-- block-id: loading-recall-lab -->
**Recall.** Why select the upper extraction bound at run start? When can a full
load be safer than incremental? Why must dimensions load before facts? Contrast
Type 1 and Type 2 for an address correction. What data must survive to replay a
stream after logic changes? For practice, write control records for one batch
increment and one streaming micro-batch, including state before, durable effects,
validation evidence, and state after.

## Loading scenario drills

Use each drill twice. First answer without looking at the explanation: name the
selection boundary, durable state, target application rule, validation equation,
failure recovery, and reconciliation. Then change one assumption—introduce
deletes, concurrent writers, late facts, or insufficient raw retention—and
redesign the pattern. A strong exam answer identifies the missing correctness
contract before choosing a Fabric tool. A strong production answer also records
who owns that contract, how it is observed, and which bounded input can be
replayed. If the design cannot explain what happens after a crash between target
write and state update, it is not yet complete.

### Timestamp ties and late commits

The source exposes millisecond `ModifiedAt`, but several rows share a timestamp
and one transaction commits late. Reading only `ModifiedAt > last_watermark`
can miss a tied row or late commit. At run start choose a fixed upper bound,
read a justified overlap from before the committed watermark, retain business
key plus source version/modified time, and select one trusted winner per key.
Apply idempotently and advance the watermark only after durable target success.

If the source offers a stable composite cursor or CDC sequence, prefer it over
ambiguous wall-clock time. Reconcile a bounded source interval and alert on
unexpected gaps. Test a row with the exact previous timestamp, two versions of
one key, and a commit visible only on the next run.

### Delete handling

An incremental source sends inserts and updates but no delete flag. The target
will accumulate records removed upstream. Options include source CDC/tombstones,
a periodic key snapshot and anti-join, a bounded full comparison, or a business
rule that never physically deletes and instead closes validity. Choose from
source semantics and analytical requirements; a modified timestamp cannot infer
a row that no longer exists.

Apply deletes only after validating scope and controls. An unexpectedly empty
snapshot could otherwise delete everything. Record deleted/expired counts,
protect required history, and make replay deterministic. Full loads naturally
reconcile absence when replace semantics are safe, which can make them preferable
for small tables.

### Type 2 correction versus real change

A customer address was entered incorrectly yesterday and corrected today. If
the organization wants historical reports to show the corrected address for all
time, treat it as Type 1 correction. If the customer genuinely moved and reports
must preserve the old address for prior facts, use Type 2: expire the current
row and add a new version. The source must distinguish correction from business
change or the warehouse needs an explicit policy.

Test nonoverlapping validity, one current row, surrogate-key lookup at boundary
times, and facts arriving after the dimension but carrying earlier event time.
Do not use load time as business validity without acknowledging the consequence.

### Streaming logic change and replay

A bug undercounted events for three days. The current checkpoint faithfully
records progress through incorrect logic. Replaying requires retained raw events,
the affected source range, corrected code version, compatible/new checkpoint,
and a target plan that replaces or idempotently restates affected results. Simply
deleting the production checkpoint can replay more history than intended and
duplicate side effects.

Build corrected output in isolation, reconcile to raw controls, atomically
publish or replace the affected partitions, and retain old/new version evidence.
The recovery design proves why raw retention and deterministic sink keys are
part of the loading contract, not optional observability.

## Exam distinctions

- Full versus incremental describes selection and application, not a specific Fabric tool.
- A timestamp watermark is not the same as Spark's event-time watermark, though both bound progress.
- SCD Type 1 overwrites; Type 2 preserves history through new dimension versions.
- A surrogate key is warehouse-managed; a business key comes from the business/source domain.
- Checkpointing supports recovery; idempotent target logic prevents duplicate effects.

## Active recall

1. When should the persisted high-water mark advance?
2. Why is a timestamp overlap window paired with deduplication?
3. State the grain of an order-line fact table.
4. How does a fact arriving before its dimension remain loadable?
5. What is the cost of setting a streaming watermark too aggressively?

## Authoritative sources

- [Load tables in a dimensional model](https://learn.microsoft.com/en-us/fabric/data-warehouse/dimensional-modeling-load-tables)
- [Choose a data movement strategy](https://learn.microsoft.com/en-us/fabric/data-factory/decision-guide-data-movement)
- [Stateful processing with Structured Streaming](https://learn.microsoft.com/en-us/fabric/data-engineering/structured-streaming-stateful-processing)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
