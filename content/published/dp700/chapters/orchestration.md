# Orchestrate processes

<!-- block-id: orientation -->
Orchestration coordinates work; transformation changes data. Choose the smallest tool that expresses the work clearly, then use a pipeline when multiple activities need dependencies, retries, parameters, observability, or a trigger.

## Objective coverage

| Measured objective | What to master |
| --- | --- |
| Choose between Dataflow Gen2, a pipeline, and a notebook | Low-code shaping, workflow coordination, and code-first distributed processing |
| Design and implement schedules and event-based triggers | Time-driven versus event-driven execution, concurrency, idempotency, and late events |
| Implement orchestration patterns with notebooks and pipelines, including parameters and dynamic expressions | Parent-child workflows, metadata-driven loops, dependencies, parameters, variables, and expressions |

## Choose between Dataflow Gen2, a pipeline, and a notebook

| Tool | Primary strength | Choose it when | Do not confuse it with |
| --- | --- | --- | --- |
| Dataflow Gen2 | Visual Power Query transformations | Analysts need repeatable tabular shaping and managed destinations | A general workflow scheduler |
| Pipeline | Coordination and data movement | Activities require ordering, branching, copying, retry, or triggers | The compute engine that performs every transformation |
| Notebook | Code-first Spark/Python/SQL work | Logic is complex, iterative, library-driven, or distributed | A no-code control plane |

A pipeline can invoke a notebook or Dataflow Gen2 activity. That nesting is often the correct answer: the pipeline owns control flow while the invoked item owns transformation logic. Avoid putting complex business rules into dynamic expressions merely because the pipeline can evaluate them.

## Design and implement schedules and event-based triggers

A schedule starts work from a clock: hourly, daily, or another recurrence. It fits predictable availability and periodic reconciliation. An event-based trigger starts from an occurrence such as a file arrival. It reduces polling delay but requires careful event filtering and duplicate handling.

| Requirement | Prefer | Design concern |
| --- | --- | --- |
| Source closes its books nightly | Schedule | Time zone, daylight saving, and source completion |
| Process each arriving object quickly | Event trigger | Duplicate/out-of-order events and partially written files |
| Guarantee eventual completeness | Scheduled reconciliation, possibly alongside events | Reprocess a bounded watermark safely |

Triggers do not guarantee business correctness. Design the target operation to be **idempotent**: rerunning the same logical input should not duplicate facts or corrupt state. Record a run ID, source object/version, high-water mark, and outcome. Set concurrency according to whether activities and targets can safely overlap.

## Implement orchestration patterns with notebooks and pipelines, including parameters and dynamic expressions

Parameters are immutable inputs for a run. Variables are mutable values used during pipeline execution. System variables expose context such as the pipeline run ID and trigger time. Dynamic expressions combine these values to construct paths, queries, and activity inputs.

```text
@concat(pipeline().parameters.basePath, '/',
        formatDateTime(pipeline().TriggerTime, 'yyyy/MM/dd'), '/')
```

Keep configuration typed and explicit. Validate required parameters at the boundary. Do not pass secrets as ordinary parameters or print them into logs.

### Reusable patterns

**Parent-child pipeline:** a parent validates shared inputs and invokes specialized child pipelines. This reduces duplication and provides one operational entry point.

**Metadata-driven ingestion:** a lookup reads enabled datasets; a ForEach invokes a parameterized copy or notebook for each row. Bound concurrency to source and capacity limits, and capture per-dataset results.

**Notebook chain:** a pipeline passes primitive parameters to a notebook, waits for its outcome, and branches on success or failure. Make the notebook return a small status contract rather than parsing arbitrary log text.

**Dependency graph:** success, failure, completion, and skip conditions determine which activity runs next. Add a deliberate failure path that records diagnostic context and alerts an owner. A retry is appropriate for transient faults; it is harmful for deterministic schema or permission failures.

### Scenario walkthrough

A daily sales load receives `businessDate` and `fullReload` parameters. The pipeline checks that the landing file exists, invokes a notebook to validate schema, runs a parameterized copy for valid data, invokes a SQL procedure to merge the target, and records the watermark only after the merge succeeds. An event trigger provides low latency, while a nightly scheduled run reconciles missing events. Because the merge key is stable, either path can retry safely.

## Tool selection as a separation of concerns

<!-- block-id: choose-tool-model -->
The three tools sit at different layers. **Dataflow Gen2** is a visual,
Power Query-based transformation experience with managed destinations.
**Notebook** is a code-first execution surface for Spark, Python, and SQL logic.
**Pipeline** is a control plane that moves data and coordinates activities.
The fact that a pipeline can copy data or evaluate an expression does not make
it the best home for complex transformation logic; the fact that a notebook can
call APIs does not make it a maintainable enterprise scheduler.

<!-- block-id: choose-tool-operations -->
Begin with the unit of work. If a business analyst can express repeatable
tabular shaping in Power Query and use a supported destination, prototype a
Dataflow Gen2. If the work requires distributed computation, custom libraries,
complex testing, or code reuse, create a notebook and parameterize its inputs.
When two or more activities require dependencies, data movement, retries,
branching, parameters, or schedules, put the control flow in a pipeline and
invoke the transformation item. Give the pipeline identity access to each
invoked item and data endpoint; do not embed secrets in expressions.

<!-- block-id: choose-tool-decisions -->
Select by maintainability as well as capability. Dataflow Gen2 improves visual
accessibility but complicated M expressions can become difficult to test.
Notebooks provide flexibility but require software discipline and can incur
Spark startup cost. Pipelines provide operational visibility but deeply nested
activities and business rules in expression strings become brittle. A common
design is pipeline → parameterized notebook or Dataflow Gen2 → governed
destination. Use a single tool when it genuinely owns the whole job; adding an
orchestrator to one simple transformation can create needless failure points.

<!-- block-id: choose-tool-example -->
**Worked decision.** A CSV requires column renaming, type conversion, a lookup
join, and loading to a warehouse table. A Dataflow Gen2 is suitable when the
volume and transformations fit its connectors and the owning team works in
Power Query. If the lookup is a very large Delta table and the logic uses a
tested Python library, choose a notebook. If the file must first be copied from
an on-premises source, the transform run after validation, and an alert sent on
failure, use a pipeline to coordinate the chosen transformer. The tool decision
is about responsibilities, not a contest for one universal winner.

<!-- block-id: choose-tool-diagnostics -->
When a solution becomes hard to operate, look for logic at the wrong layer:
hundreds of pipeline expressions, a notebook reimplementing scheduling and
retry, or a Dataflow whose steps hide an opaque procedural algorithm. Inspect
run history at the orchestration layer and the invoked item's detailed logs at
the compute layer. As a mini-lab, implement the same three-column cleanup once
in a Dataflow and once in a notebook, then write a pipeline that invokes one;
compare authoring, testability, startup, lineage, and error evidence.

## Trigger engineering

<!-- block-id: triggers-model -->
A schedule asserts that **time is the readiness signal**. An event trigger
asserts that **an observed event is the readiness signal**. Neither proves that
all business inputs are complete. Scheduled runs must reason about time zone,
daylight-saving transitions, source close times, and overlap. Event-driven runs
must reason about event filtering, duplication, ordering, partial writes, and
bursts. A reconciliation schedule often complements events because delivery
systems can be at-least-once or temporarily unavailable.

<!-- block-id: triggers-operations -->
For a schedule, define recurrence, start and end boundaries, time zone, missed
run policy, expected duration, and safe concurrency. For an event trigger,
select the event source, filter to the intended objects, pass stable event
metadata into pipeline parameters, and validate that the object is ready before
processing. In both cases, generate or receive an idempotency key, persist the
source version and watermark, and make retries safe. Configure monitoring for
failed, unusually long, and unexpectedly absent runs.

<!-- block-id: triggers-decisions -->
Prefer schedules for periodic snapshots, closed accounting periods, and
reconciliation. Prefer events for low-latency response to discrete arrivals.
Use both when fast processing and eventual completeness matter. Prevent overlap
when the target uses destructive replace semantics; allow controlled
concurrency when inputs and target partitions are independent. A “file created”
event can fire before an upstream multi-file delivery is complete, so use a
manifest, completion marker, stable-size check, or upstream contract rather
than an arbitrary delay.

<!-- block-id: triggers-example -->
**Worked trigger.** An event arrives for this object:

```text
landing/region=CA/business_date=2026-09-01/orders.parquet
```

It passes the URL, event ID, and modification timestamp to a pipeline. The first activity rejects
unexpected paths and checks a control table keyed by URL plus version. A valid
new object is processed and the key recorded atomically. A duplicate event
finds the completed key and exits successfully without inserting rows again. A
02:00 scheduled reconciliation compares the manifest with processed keys and
submits only missing versions.

<!-- block-id: triggers-diagnostics -->
For a run that never started, inspect whether the trigger is enabled, its time
zone or event subscription, filter, source event, and permissions. For duplicate
runs, compare event IDs and business idempotency keys; do not simply increase a
delay. For overlapping schedules, compare trigger time, actual start time,
duration, queueing, and concurrency settings. A useful mini-lab is to submit the
same event twice and prove the target has one logical result, then intentionally
withhold an event and prove reconciliation finds it.

## Parameterized orchestration patterns

<!-- block-id: patterns-model -->
Parameters are run inputs and should be treated as immutable. Variables hold
mutable run state. System variables expose orchestration context. Dynamic
expressions resolve values from parameters, activity outputs, variables, and
system context at runtime. A parent-child pattern centralizes common control
flow; a metadata-driven pattern turns configuration rows into repeated work;
fan-out/fan-in runs independent units in parallel and then joins their results.

<!-- block-id: patterns-operations -->
Define parameter names, types, defaults, allowed values, and ownership before
building expressions. Validate required inputs in the first activity. Pass only
the values a child requires and return a small, documented result. In a
metadata-driven pipeline, look up enabled configuration rows, iterate with a
bounded concurrency, and parameterize datasets, paths, or notebook arguments.
Use activity dependencies for success, failure, completion, and skip paths.
Route secrets through managed connections or secret integration, mask sensitive
outputs, and include the pipeline run ID in operational records.

<!-- block-id: patterns-decisions -->
Use a parent-child pipeline when the child is a coherent reusable workflow, not
merely to reduce the number of boxes on screen. Use metadata-driven iteration
when many entities share one algorithm and differ in configuration. Use
fan-out/fan-in only when target isolation and capacity support parallelism.
Prefer explicit expressions over clever nested expressions, and calculate
complex business logic in a tested transform. Parameters configure behavior;
copying whole environment-specific JSON documents into them can create an
unreviewed second configuration system.

<!-- block-id: patterns-example -->
**Worked pattern.** A control table contains `entity`, `source_path`,
`target_table`, `watermark_column`, and `enabled`. The parent looks up enabled
rows and invokes child `load_entity` with those five typed values. The child
reads the previous watermark, copies the bounded range to staging, validates
counts, merges into the target, advances the watermark only after success, and
returns rows read and written. The parent aggregates results and fails if any
required entity failed. Rerunning one entity uses the same algorithm and a
deliberate watermark override.

<!-- block-id: patterns-diagnostics -->
Expression failures often come from the wrong evaluation context, null activity
output, incorrect JSON path, unintended string conversion, or escaping. Inspect
the resolved activity input in run details rather than only the expression
source. For a failed child, retain both parent and child run IDs. For loops,
record the current entity and concurrency. Reproduce with one known metadata row
before scaling out. A mini-lab should process two entities, force one child to
fail, confirm the parent captures both results, and rerun only the failed unit
without duplicating the successful target.

<!-- block-id: orchestration-exam-distinctions -->
On the exam, “transform with a visual Power Query experience” points to
Dataflow Gen2; “distributed custom code” points to a notebook; “coordinate,
copy, branch, retry, or trigger” points to a pipeline. Parameters are immutable
run inputs, variables are mutable run state, and dynamic expressions compute
runtime values. An event trigger reduces latency but does not remove the need
for idempotency and reconciliation.

<!-- block-id: orchestration-recall-lab -->
**Recall and mini-lab.** Why might a pipeline invoke a notebook rather than
place all logic in pipeline expressions? Give two ways to prove a multi-file
delivery is complete. What state must advance only after a successful
incremental load? Contrast an event ID with a business idempotency key. Finally,
draw a parent pipeline with lookup, bounded fan-out, child invocation, failure
collection, and a reconciliation trigger; label parameters, variables, and
system values.

## Orchestration scenario drills

### Choose the owner of each responsibility

A finance process copies eight source tables, applies dimensional logic, and
publishes a quality summary. Use a pipeline to own schedule, dependencies, Copy
activities, parameters, retry classification, and failure routing. Use a
notebook or warehouse SQL procedure for code-first/set-based dimensional logic.
Use Dataflow Gen2 only where its visual Power Query transformations and supported
destinations improve maintainability. Do not translate tested SQL into dozens of
pipeline expressions.

Define one run contract: business date, full/incremental flag, source upper
bound, target environment, and correlation ID. The pipeline passes only required
typed values; transformations return small status/count outputs. Success requires
quality and reconciliation, not merely every activity turning green.

### Event burst and duplicate delivery

Ten thousand object-created events arrive after a source outage, including
duplicates. An unbounded trigger-to-run design overwhelms the source and sink.
Filter expected paths, validate a stable object/version idempotency key, and
control run concurrency. A completed key exits successfully; an in-progress key
prevents unsafe overlap; a failed key is retriable according to target semantics.

If events can describe partially written objects, require a manifest/completion
marker or other readiness contract. A later scheduled reconciliation compares
expected versus processed objects and submits gaps. Monitor event rate, queued
runs, source/sink throttling, duplicate suppression, failed keys, and freshness.

### Metadata-driven loading with one bad entity

A control table lists 40 entities. One row references a removed source column.
The parent lookup returns enabled rows and invokes a parameterized child with
bounded ForEach concurrency. The child validates metadata, extracts, stages,
checks schema, applies target changes, and returns counts. Thirty-nine succeed;
one fails deterministically.

The parent records each result and fails the required overall run without
reapplying successful entities. Repair the metadata/source contract and rerun
only the failed entity. A blanket retry of the ForEach would waste capacity and
could duplicate outputs if sinks are not idempotent. Retain parent and child run
IDs to correlate the incident.

### Clock schedule across daylight saving

A daily job must run after a source closes at 01:30 local time, in a region with
daylight-saving transitions. Specify the business time zone explicitly and
decide behavior for the repeated or missing local hour. Better, use the source's
published completion signal when available and keep a cutoff reconciliation.
Record logical business date separately from UTC trigger timestamp.

Prevent concurrent runs when the job replaces the same partition; allow parallel
business dates only if target isolation is proven. Alert on “no successful
business date by cutoff,” which catches a missing trigger as well as a failed
run. A simple alert on activity failure cannot detect a run that never started.

## Capstone: metadata-driven retail ingestion

A retailer receives daily customer and product snapshots, hourly order files,
and near-real-time shipment events. Build one operating design without forcing
all three sources through the same pattern.

### Requirements and proposed design

- Customer and product snapshots close at 02:00 local business time and must be
  available before fact processing.
- Order files arrive by region and can be redelivered with the same object
  version. All regions must be complete by 05:30.
- Shipment events should appear within five minutes, but correctness by next
  morning matters more than never missing an event.
- Development, Test, and Production use different connections; credentials must
  not appear in parameters or logs.

Use a scheduled parent pipeline for snapshot dimensions. It validates the
business date, invokes parameterized child loads, checks uniqueness and counts,
and publishes a dimension-ready control only after both dimensions succeed. Use
event-triggered order ingestion keyed by object URL plus version, with bounded
concurrency and an idempotent target merge. A 04:30 reconciliation pipeline
compares the regional manifest with completed keys. Use Eventstreams or Spark for
continuous shipment processing, retain raw events, and schedule a bounded replay
comparison before the 05:30 cutoff.

Connections or variable libraries provide environment configuration where
supported; a governed credential mechanism owns secrets. Parameters carry
business date, entity, object reference, source upper bound, and correlation ID.
Variables hold only mutable run state such as collected failure count. System
variables supply pipeline/trigger identifiers.

### Control tables

Design three small contracts:

```text
entity_config(entity, source, target, load_type, watermark_column, enabled)
object_run(object_url, object_version, business_date, status, pipeline_run_id)
batch_control(entity, lower_bound, upper_bound, rows_read, rows_written,
              rows_rejected, status, committed_at)
```

The parent reads enabled configuration and passes one typed row to each child.
The child selects a fixed interval, stages, validates, writes idempotently, and
commits its watermark after target success. `object_run` enforces duplicate
suppression. Do not use a pipeline variable as the durable watermark; variables
disappear with the run and are unsafe under concurrency.

### Failure injections

1. Deliver one order file twice. The second event should find the completed
   object/version and exit without another logical write.
2. Make one region's schema incompatible. Other independent regions may finish,
   but the cutoff reconciliation reports the missing required region and blocks
   readiness.
3. Crash after target merge but before watermark update. A rerun reads the same
   range and produces the same target through stable keys.
4. Withhold a shipment event from the trigger path while retaining it in raw
   source. The scheduled comparison discovers and replays it.
5. Expire a Test connection. Deployment remains successful, while the runtime
   smoke test fails authorization and prevents promotion.

### Monitoring and acceptance

Monitor schedule/trigger state, queue and activity duration, source rows/files,
input/output, rejects, watermarks, duplicate suppressions, reconciliation gaps,
stream lag, and consumer-visible freshness. Each failure alert carries
environment, entity/object, run ID, source boundary, first failing activity, and
runbook. A separate cutoff alert catches missing runs.

The capstone is accepted only when every failure can be replayed from the
smallest safe boundary; secrets remain outside ordinary parameters; duplicate
delivery changes no totals; all control equations reconcile; and Test deployment
plus runtime/data checks pass. This is the central orchestration idea: the
pipeline coordinates evidence-backed state transitions while the selected
compute tool owns transformation.

## Exam distinctions

- A schedule answers *when*; an activity dependency answers *after what*.
- An event trigger reduces polling but does not eliminate duplicate-event or partial-file risks.
- Parameters do not change during a run; variables can.
- Pipeline expressions configure and route work; notebooks and dataflows normally hold substantial transformation logic.
- Retries address transient failures. Fix authentication, invalid schemas, and bad expressions instead of retrying them repeatedly.

## Active recall

1. Which tool owns ordering when a Dataflow Gen2 must run before a notebook?
2. Why pair an event trigger with scheduled reconciliation?
3. When is a pipeline variable more appropriate than a parameter?
4. What makes a metadata-driven ForEach safe to rerun?
5. Which evidence distinguishes a transient failure from a deterministic one?

## Authoritative sources

- [Pipeline overview](https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-overview)
- [Parameters for Data Factory in Fabric](https://learn.microsoft.com/en-us/fabric/data-factory/parameters)
- [Data Factory overview](https://learn.microsoft.com/en-us/fabric/data-factory/data-factory-overview)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
