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
