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

## Pipeline failure clinic

<!-- block-id: resolve-pipeline-comprehensive -->
A pipeline run is a graph of resolved activities, not just a canvas definition.
Start with run ID, trigger, parameters, identity, and the earliest failed
activity. Open its resolved input/output and exact error code. Trace a child
pipeline or notebook using its child run ID. Validate dynamic-expression type
and JSON path, source/sink connection, path/table, mapping, target constraints,
timeout, retry, and concurrency. Do not expose secret values while capturing
evidence.

Classify before repair: permission/authentication requires identity or connection
correction; missing/renamed input requires source contract or routing; mapping
and constraint failures require schema/data handling; throttling and temporary
network faults may use bounded backoff. For partial ForEach completion, enumerate
successful units and prove target idempotency before replay. A retry cannot make
an invalid column mapping valid.

**Lab.** A metadata-driven child receives `sourcePath=null`, so `concat()` builds
an unintended path and Copy fails “not found.” Capture the lookup output and
resolved child input, add boundary validation, correct the metadata, and rerun
only that entity. Then simulate throttling and verify backoff succeeds without
duplicate rows. The regression checks both null rejection and repeat-safe
application. If the activity remains queued, add capacity, integration runtime,
and concurrency evidence rather than changing the path again.

## Dataflow Gen2 failure clinic

<!-- block-id: resolve-dataflow-comprehensive -->
Separate **author/save validation**, **refresh execution**, and **destination
write**. In refresh history identify the run, failing query, first failing step,
connection/gateway, and detailed log. Reproduce on the offending query and data,
not only the small preview. Test credentials and privacy/firewall boundaries,
then schema names/types, locale conversions, merge cardinality, custom functions,
folding/source timeout, and destination schema/update behavior.

An added source column may be harmless while a removed/renamed or changed-type
column is breaking. Replacing every error with null can turn a visible failure
into silent corruption. Route conversion failures with source value, reason,
run, and rule; correct or approve disposition. If refresh is slow rather than
failed, inspect folding, source rows/bytes, gateway routing, and destination
write. Some connectors report rows and others bytes, so do not compare unlike
statistics.

**Lab.** Preview contains 1,000 valid dates, while the full source contains
`31/13/2026`. Refresh fails at `Changed Type`. Create an errors query, apply an
explicit locale, quarantine the invalid row, and reconcile accepted plus rejected
to source. Next rename a source column and prove schema validation fails before
publish. The correct regression includes the previously unseen value, not just
another preview.

## Notebook and Spark failure clinic

<!-- block-id: resolve-notebook-comprehensive -->
Identify whether failure occurs before session start, in the driver/cell, or in
distributed stages/tasks. Pre-session failures point to pool/capacity,
environment runtime, library publication, permissions, or lakehouse attachment.
A driver stack trace points to Python/SQL/control logic or collecting too much
data. Repeated executor/task failure points to one bad record/partition, skew,
shuffle, memory, serialization, or transient worker loss. Use Spark UI and logs
for the first failing stage and compare task duration, input, shuffle, spill, and
failure reasons.

Confirm code version, parameters, runtime, published environment, libraries,
Spark configuration, attached item, identity, input partition, and checkpoint
for streaming. Avoid `collect()`/`toPandas()` on unbounded data; filter/project
early; replace Python UDFs with built-ins where possible; isolate corrupt input;
fix skew before scaling. A library that imports interactively but is absent from
the published environment will fail scheduled execution.

**Lab.** One key holds 70% of rows. The Spark stage shows one task far longer
than its peers and spilling, while executor utilization elsewhere is low.
Preaggregate or redesign the key; if legitimate, use a measured skew strategy
such as adaptive execution or selective salting. Compare task distribution and
correct totals before/after. Separately force a driver OOM with a test `collect`
and repair it with distributed aggregation; explain why adding executors would
not increase driver memory.

## Eventhouse failure clinic

<!-- block-id: resolve-eventhouse-comprehensive -->
Split ingestion, command/policy, query, and capacity. Eventhouse monitoring can
expose metrics plus command, data-operation, ingestion-result, and query logs.
For ingestion, keep source/connection, database/table, operation/request ID,
format and ingestion mapping, schema/type, identity, batching, and result. For a
query, keep request ID, database context, text, time range, scanned/result rows,
duration, and error. Check that event time—not ingestion time—is used as intended.

Mapping name, delimiter/encoding, dynamic JSON path, unsupported type, missing
table permission, source connectivity, and retention/caching policy can fail or
misroute ingestion. An empty query can result from the wrong database/table,
too-narrow time filter, time-zone/parse error, or ingestion delay. Reduce a
failing KQL pipeline operator by operator; start with `take` and a known broad
time range, then reapply filters and parsing.

**Lab.** Five events are sent; four ingest and one rejects because
`Temperature="hot"` conflicts with mapping. Locate the ingestion result, retain
the source position, correct or route the event, and reconcile five outcomes.
Then query a future event-time range and prove empty results are a query-boundary
issue, not ingestion failure. If all databases slow simultaneously, examine
Eventhouse system/capacity evidence before rewriting one mapping.

## Eventstream failure clinic

<!-- block-id: resolve-eventstream-comprehensive -->
Walk the graph and compare rate at every boundary: source connected/input,
operator input/output/error, route match, destination accepted/failed, and
end-to-end lag. Capture item, time, source partition/offset or event ID,
event-time/schema version, and destination status. Validate connector credentials
and network, then transformation fields/types, window time/watermark, route
conditions, and destination permissions/capacity.

A flat zero input points upstream; normal source input and zero after an operator
points to filter/schema logic; normal branch output plus destination failures
points downstream. Rising lag with input greater than output indicates
backpressure or a slow sink, not necessarily lost events. Route poison messages
to a restricted quarantine with reason and replay reference; do not create an
infinite retry loop around deterministic bad payloads.

**Lab.** Rename `eventTime` to `event_time` at the source without updating the
window transform. Raw route continues, curated output stops. Boundary rates
localize the first zero-output operator. Add schema validation/version handling,
replay retained raw events, and verify window totals. Then deny only one
destination and show the healthy branch continues; the incident scope is one
sink, not the entire stream.

## T-SQL failure clinic

<!-- block-id: resolve-tsql-comprehensive -->
Capture statement/query ID, database and schema context, executing identity,
parameters, exact number/message, transaction state, and time. Compilation/name
errors differ from permission, conversion, constraint, blocking/deadlock,
resource, and timeout failures. Query Monitor, query insights, DMVs, or plans
provide runtime evidence where supported. Use the least-privilege grant rather
than changing ownership or granting a broad workspace role.

For truncation/conversion, find the column and offending value, compare source
and target types/length/precision, and choose validated cleansing or schema
change. For key/null constraints, test staged uniqueness and required values
before the target. For deadlocks, keep the graph/context, make transaction order
consistent and transactions short, and use safe retry only for the chosen
victim. For timeout, separate client timeout, blocking, capacity queueing, scan,
and plan regression.

**Lab.** Two staged rows share a target business key and `MERGE` fails. Rank to
one trusted source version, quarantine ambiguous ties, enforce the invariant,
and rerun idempotently. Then create a safe blocking scenario in a test database,
identify blocker versus victim, and resolve transaction scope rather than adding
an index at random. Regression fixtures retain the duplicate key and verify one
deterministic outcome.

## Shortcut failure clinic

<!-- block-id: resolve-shortcut-comprehensive -->
A shortcut failure spans reference metadata, connection identity, source target,
format, consuming engine, and optional cache/acceleration. Record shortcut/item,
target URI/path, internal versus external type, connection, querying identity,
engine, schema, and exact error. Confirm target existence first, then connection
validity and source ACL, supported location/format, Delta `_delta_log` for table
use, Tables versus Files placement, and schema/cache status.

Different users can see different results because credential delegation and
permissions differ. Deleting a shortcut is not target recovery; moving the
target requires updating/recreating the reference. For KQL validate
`external_table()` and time/schema assumptions; for accelerated shortcuts check
cache status/window and external-table limitations separately. A standard
shortcut cannot hide source outage or latency.

**Lab.** Query a known Delta shortcut, revoke the connection identity's source
read, and confirm an authorization failure while target files remain. Restore
read, then remove `_delta_log` in a disposable copy and show file access may not
qualify as a table. Repair the test target and validate row count and schema.
Record a denied identity as well as the allowed one so success is not proved only
with owner privileges.

<!-- block-id: errors-exam-distinctions -->
Resolved pipeline inputs show runtime truth; Dataflow preview is sampled authoring
evidence; Spark UI separates driver, stage, and task behavior; Eventhouse
ingestion logs differ from query logs; Eventstream boundary rates localize graph
failures; T-SQL error/plan context distinguishes correctness from slowness; a
shortcut is a reference whose target can remain intact. Retry only a classified
transient fault and only with repeat-safe effects.

<!-- block-id: errors-recall-lab -->
**Recall.** What is the earliest-failure rule? Why can `collect()` cause driver
rather than executor failure? Which Eventhouse evidence proves a rejected event?
How do Eventstream boundary rates distinguish source from destination? What
makes a T-SQL timeout ambiguous? Which three identities/permissions can affect a
shortcut path? For practice, write one incident record with time, scope,
correlation ID, classification, evidence, correction, rerun boundary, outcome,
and regression test.

## Cross-item incident drills

### The downstream cascade

A pipeline Copy fails authentication. Its notebook dependency is skipped, the
warehouse procedure never runs, and the semantic refresh later fails because a
staging table is absent. Start at the earliest pipeline authentication failure,
not the final semantic error. Identify the connection identity, credential
state, source permission, and whether rotation or ownership changed. Repair and
rerun from the smallest repeat-safe boundary.

After recovery, validate copied counts, notebook output, warehouse transaction,
and model freshness. Add credential ownership/rotation monitoring and a pipeline
failure alert. The later errors are useful impact evidence but not separate root
causes.

### Intermittent versus data-dependent

A notebook task fails on roughly the same partition every retry. Increasing
automatic retries makes the run longer but not more reliable. Compare failed
task input/key range and exception. If the same malformed record, oversized
group, or serialization path recurs, classify deterministic and isolate/correct
it. If different workers fail with transient service/network evidence, bounded
retry may be appropriate.

Build a small fixture containing the failing record or skewed key and preserve
it as regression input. A production retry policy should not conceal the
difference between repeatable code/data faults and genuinely transient worker
loss.

### Permission denied after deployment

A pipeline worked in Development but fails in Test with access denied. The
definition and parameters deployed, but target connection/identity permission
did not. Compare resolved Test connection, executing identity, gateway/source
ACL, workspace/item permissions, and secret binding. Do not grant Contributor
to make one source read work.

Apply the narrow connection or data permission, test the allowed operation and
a denied alternate operation, and add the binding/permission check to release
smoke tests. Deployment success and runtime authorization are different gates.

### Empty KQL result after successful ingestion

Eventhouse ingestion metrics show accepted events, but the query returns none.
Start with the correct database/table and `take` or a broad known time range.
Inspect ingestion time and parsed event time, then add each `where`, dynamic
parse, and join operator one at a time. A future time-zone conversion or null
event-time filter can eliminate every row.

Retain the request/query ID and input/result counts at each reduction. If a
broad query is also empty, return to ingestion mapping/table evidence. This
prevents changing a working ingestion path to repair a query-boundary problem.

### Shortcut works for owner only

The creator can query an external shortcut, while consumers receive denied
errors. Enumerate creator elevation, consumer workspace/item/OneLake permission,
connection credential mode, and source ACL. Test with a clean representative
consumer rather than impersonating through an owner session. Confirm Tables
versus Files and engine-specific requirements after authorization is understood.

Do not solve it by sharing source credentials or granting broad workspace
write. Choose the supported least-privilege credential/access design, rotate it
through governed ownership, and preserve a negative test.

### Repair without losing incident evidence

During an outage, responders are tempted to edit multiple parameters, delete a
checkpoint, recreate a shortcut, and scale capacity simultaneously. That can
erase the causal trail. Preserve run/request IDs, logs, resolved values,
checkpoint/target metadata, source version, and timestamps first. Change one
hypothesized cause in a safe scope and compare the outcome.

Emergency restoration can justify a faster roll-forward or rollback, but record
each action and its evidence. After service returns, reproduce the fault safely,
add a regression, update the runbook, and remove temporary excess permission or
capacity.

## Capstone: one incident, seven surfaces

At 03:10, a source schema release changes `CustomerId` from integer to text and
renames `eventTime`. The batch pipeline maps the old integer, Dataflow performs
an implicit type conversion, a notebook joins on mismatched types, Eventstream
windows reference the old field, Eventhouse receives some malformed records, a
warehouse procedure encounters conversion errors, and a lakehouse shortcut still
points to valid source data. Several red symptoms share one upstream change but
must be proven, not assumed.

### Evidence funnel

Record incident window, deployment/source version, affected workspace/items,
identities, pipeline/Dataflow/Spark/Eventhouse/query IDs, and consumer impact.
Find the earliest boundary: source contract versus pipeline resolved mapping.
Then trace each branch:

- Pipeline: old mapping and resolved inputs fail conversion. Update the explicit
  contract after source ownership confirms the change.
- Dataflow: preview may not include new values; refresh detail identifies the
  first conversion or renamed-column step. Use explicit text handling and a
  quarantine query.
- Notebook: Spark plan/tasks show join keys with incompatible types. Normalize
  once at the validated boundary, not through scattered casts.
- Eventstream: raw input continues, but curated output falls to zero after the
  window operator because `eventTime` is absent. Version/normalize before
  windowing and replay raw retained events.
- Eventhouse: ingestion results distinguish accepted from mapping/type rejects;
  KQL query logs are not the source of ingestion truth.
- T-SQL: preserve error number/message and offending staged values; correct
  staging type/mapping before target constraints.
- Shortcut: verify target/path/connection and known query. If it still works,
  do not recreate it just because adjacent consumers fail schema expectations.

### Recovery plan

Freeze the committed batch watermark if target application did not succeed.
Deploy compatible normalization to Test, run a fixture containing legacy and new
schema versions, and compare explicit dispositions. Replay the bounded batch
range idempotently. Replay streaming raw events from the source/version boundary
using controlled checkpoint/target state. Reconcile source = accepted +
quarantined, warehouse totals, window counts, and consumer freshness.

Avoid broad retry while deterministic mappings remain wrong. Avoid editing all
seven items independently when a shared schema adapter/contract boundary can
normalize both versions. Keep the last known-good published output until the
corrected version passes controls.

### Regression and post-incident controls

Store the breaking records as sanitized fixtures. Add pre-publish schema-
compatibility tests, explicit type/field assertions, Dataflow error-rate checks,
notebook join-key tests, Eventstream schema-version routing, Eventhouse ingestion-
reject alerting, staging constraints, and end-to-end freshness/reconciliation.
Update source change notification and release coordination.

The incident closes only when every surface is classified as root cause,
consequence, or unaffected; all affected source data has a disposition; replay
is repeat-safe; consumer output is fresh and correct; temporary changes are
removed; and the exact breaking schema change can no longer pass the regression
gate unnoticed.

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
- [Spark errors overview in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/data-engineering/troubleshoot-spark)
- [Manage and monitor a KQL database](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/manage-monitor-database)
- [Real-Time Intelligence overview](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview)
- [Troubleshoot Fabric Data Warehouse](https://learn.microsoft.com/en-us/fabric/data-warehouse/troubleshoot-fabric-data-warehouse)
- [OneLake shortcuts](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
