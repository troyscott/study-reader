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
