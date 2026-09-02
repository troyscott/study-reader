# Identify and resolve errors

<!-- block-id: orientation -->
Troubleshooting is an evidence funnel: define the symptom and scope, identify the failing component, capture the most specific error and correlation ID, classify the fault, change one cause, and rerun the smallest representative case.

## Objective coverage

| Measured objective | First evidence |
| --- | --- |
| Identify and resolve pipeline errors | Failed activity, inputs/outputs, parameters, error code, and child run |
| Identify and resolve Dataflow Gen2 errors | Refresh detail, failing query/step, connector, schema, and destination |
| Identify and resolve notebook errors | Spark application, failed cell/stage/task, driver/executor log, and environment |
| Identify and resolve Eventhouse errors | Ingestion failure, KQL error, table policy, extent, and capacity evidence |
| Identify and resolve Eventstream errors | Source/destination status, event schema, transformation, and throughput |
| Identify and resolve T-SQL errors | Error number/message, query text, permissions, schema, and execution plan |
| Identify and resolve OneLake shortcut errors | Target path, connection, source permission, format/schema, and cache status |

## A repeatable diagnostic method

1. Record time range, workspace/item, run/query ID, identity, and visible symptom.
2. Decide whether one record, one item, one workspace, or the capacity is affected.
3. Find the earliest failing component; downstream errors are often consequences.
4. Classify: authentication/authorization, connectivity, schema/data, expression/code, resource/capacity, concurrency, or transient service.
5. Reproduce with the smallest safe input and preserve the original evidence.
6. Apply a targeted correction, rerun, and add a regression check.

## Identify and resolve pipeline errors

Open the run and failed activity. Inspect resolved inputs and outputs rather than only the activity definition. Validate parameter types, dynamic expression results, connection identity, source/sink paths, mappings, and child pipeline/notebook run IDs.

Use retries for throttling, temporary connectivity, or service unavailability. Fix invalid expressions, missing files, denied permissions, incompatible mappings, and constraint violations. If a ForEach partially succeeds, rerun only when the target is idempotent or the successful subset is excluded.

## Identify and resolve Dataflow Gen2 errors

Locate the failed refresh and query. Step through Power Query transformations to find the first error, checking source credentials/privacy, gateway, type conversions, renamed/missing columns, query folding, and destination schema/write settings.

A preview can succeed on sampled data while refresh fails on an unseen value or full volume. Profile the entire failing column or capture representative bad rows. Explicitly handle conversion errors and schema drift; do not replace all errors with null unless that loss is an approved quality rule.

## Identify and resolve notebook errors

Separate driver failures from executor/task failures. A Python stack trace in one cell suggests code or input; repeated task loss can suggest skew, bad records, memory, or infrastructure. Confirm runtime, environment publication, libraries, attached lakehouse, credentials, and Spark configuration.

For out-of-memory errors, identify whether the driver collected too much data or a partition/task is oversized. Avoid `collect()` on large results, reduce shuffle width, correct skew, prune early, and scale only after measuring. Reproduce with the same runtime and a small failing partition.

## Identify and resolve Eventhouse errors

Distinguish ingestion from query. For ingestion, inspect failures by table/source and validate mapping, format, encoding, required fields, identity, retention/caching policies, and capacity. For KQL, keep the request ID, reduce the query, verify names/types, and inspect resource/scanned-data behavior.

An empty query result is not automatically an ingestion failure: check time filters, event-time parsing, database context, and whether data landed in another table.

## Identify and resolve Eventstream errors

Follow the graph from source through transformations to each destination. Check connector state and credentials, incoming/output event rates, schema and type assumptions, malformed events, window time field, and destination health. One failing destination should be distinguished from a source that stopped producing.

Protect against poison events with validation and a quarantine route. If input exceeds output and lag grows, find the saturated transformation or destination before increasing capacity.

## Identify and resolve T-SQL errors

Capture the exact error number/message and statement. Verify database/schema context, object names, permissions, data types, nullability, key constraints, transaction state, and concurrency. For slow rather than failed queries, inspect the actual plan and runtime evidence—do not guess from SQL text alone.

Common distinctions: “invalid object” is usually context/name/deployment; “permission denied” is identity/grant; truncation/conversion is data/schema; deadlock is concurrency and transaction ordering; timeout can be client, resource, blocking, or plan related.

## Identify and resolve OneLake shortcut errors

Verify that the shortcut target still exists, the stored connection is valid, the executing identity has required OneLake/source permissions, the target format is supported in its location, and schema synchronization/caching has not encountered an incompatible change. Deleting a shortcut leaves the target; deleting or moving the target breaks the reference.

For KQL shortcuts, validate with `external_table('name')`. For lakehouse table shortcuts, confirm the target is a supported Delta table and appears at the correct Tables path. Acceleration has separate status, cache-window, and schema constraints.

## Exam distinctions

- Retry transient faults; correct deterministic faults.
- Find the earliest failure, not merely the last red activity.
- Preview success does not prove full Dataflow refresh success.
- Driver memory and executor/task memory are different Spark diagnoses.
- Eventhouse ingestion failure and KQL query failure have different evidence.
- A broken shortcut does not mean the target data was deleted.

## Active recall

1. Which pipeline view shows resolved runtime values?
2. Why can Dataflow preview pass while refresh fails?
3. What evidence separates Spark driver failure from executor failure?
4. Input rate is stable but output rate falls—where do you look in an Eventstream?
5. Which shortcut changes can break a formerly valid table?
6. What turns a production incident into a regression test?

## Authoritative sources

- [Pipeline troubleshooting guide](https://learn.microsoft.com/en-us/fabric/data-factory/pipeline-troubleshoot-guide)
- [Monitor Dataflow Gen2 refreshes](https://learn.microsoft.com/en-us/fabric/data-factory/dataflows-gen2-monitor)
- [Manage and monitor a KQL database](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/manage-monitor-database)
- [OneLake shortcuts](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
