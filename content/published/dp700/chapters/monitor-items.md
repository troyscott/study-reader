# Monitor Fabric items

<!-- block-id: orientation -->
Monitoring turns execution into evidence. Start with a service objective, then collect signals that distinguish freshness, correctness, reliability, and efficiency. A green “Succeeded” state proves execution completion—not data quality.

## Objective coverage

| Measured objective | Evidence to inspect |
| --- | --- |
| Monitor data ingestion | Run state, rows/bytes, throughput, latency, watermark, lag, and rejected records |
| Monitor data transformation | Activity/query/job status, duration, resources, input/output counts, and quality results |
| Monitor semantic model refresh | Refresh status, type, duration, partition/table detail, and failure message |
| Configure alerts | Signal, threshold, evaluation cadence, recipient/action, suppression, and recovery |

## Monitor data ingestion

Use the Fabric Monitoring hub for a cross-workspace view of supported job runs, then drill into the owning item for activity-level detail. For pipelines, inspect input/output, activity duration, copy throughput, integration runtime/gateway, and error details. For Eventstreams/Eventhouse, inspect incoming-event rate, processing lag, rejected events, destination status, and ingestion failures.

Define freshness as an observable equation:

```text
freshness lag = observation time - newest successfully published business event time
```

This is more useful than “last run succeeded.” Also compare rows read, rows written, rows rejected, and source control totals. Track the last committed watermark independently from the current attempt.

## Monitor data transformation

The right signals depend on the engine:

| Item | Operational evidence |
| --- | --- |
| Dataflow Gen2 | Refresh status, duration, query/destination failures, and destination results |
| Notebook/Spark job | Application/session state, stage/task failures, executor behavior, skew/spill, and output checks |
| Pipeline | Activity graph, dependency path, retries, parameters, copy metrics, and child-run IDs |
| Warehouse/Eventhouse query | Duration, resource use, scanned data, queuing, and query text/plan context |

Attach data assertions to the run: uniqueness, null rate, referential integrity, allowed ranges, schema contract, and reconciliation totals. Store a small quality result containing rule, severity, observed value, threshold, run ID, and disposition.

## Monitor semantic model refresh

Semantic model refresh is downstream of ingestion and transformation. Use refresh history or the administrative refresh summary to see status, start/end time, refresh type, and error detail. For large models, inspect table/partition behavior and whether incremental refresh covers the intended date range.

Classify failures before acting: expired credentials, gateway unavailable, capacity pressure, source timeout, schema change, memory pressure, or invalid query. A retry can help transient capacity/network faults; it does not repair a renamed source column.

End-to-end freshness is governed by the slowest required stage:

```text
source event -> ingestion -> transformation -> semantic refresh -> consumer-visible data
```

## Configure alerts

An actionable alert specifies the signal, threshold, evaluation window, recipient, action, deduplication/suppression, and recovery condition. Fabric Activator can evaluate events or periodic observations and trigger actions such as notifications or Power Automate flows.

Prefer sustained conditions over noisy single samples: “freshness lag exceeds 30 minutes for two evaluations” is usually better than “one run lasted 31 minutes.” Route alerts to an owner who can act, include item/run identifiers and a runbook link, and test both firing and recovery.

| Alert | Why it matters | First diagnostic |
| --- | --- | --- |
| No successful ingestion by cutoff | Consumer SLA at risk | Trigger/run history and source availability |
| Rejected-row rate above threshold | Correctness degraded | Quality rule and source sample |
| Semantic refresh failed | Published model is stale | Refresh detail and upstream completion |
| Streaming lag rising continuously | Backpressure or destination issue | Input/output rate and resource saturation |

## Monitoring model: outcome, execution, resource

<!-- block-id: monitoring-foundation -->
Every production data product needs three layers of evidence. **Outcome** asks
whether the published data is fresh, complete, valid, and available.
**Execution** asks whether the pipeline, refresh, query, or stream ran as
designed. **Resource** asks whether capacity, compute, gateway, network, source,
or destination limited it. Monitoring hub is an entry point for supported jobs;
item run detail and workspace monitoring provide deeper execution evidence;
the Capacity Metrics app provides capacity evidence. None alone proves the
business outcome.

Define a service-level indicator with an owner and unit, then a target and
measurement window. Examples include “99% of hourly partitions published within
20 minutes,” “fewer than 0.1% rejected records per daily load,” or “semantic
model ready by 07:00 on business days.” Record UTC timestamps plus business
time-zone meaning, stable item/run IDs, source version/watermark, code version,
and target version so evidence can be correlated.

## Ingestion monitoring field guide

<!-- block-id: monitor-ingestion-comprehensive -->
Monitor batch ingestion as a control equation: selected source rows/files =
accepted + quarantined + explicitly ignored, and accepted should reconcile to
the target application semantics. Record bytes/rows read and written, files,
duration, throughput, watermark range, retries, rejects, and publish time. For
streaming, add input and processed rates, end-to-end/event-time lag, backlog,
late or dropped events, state size, checkpoint progress, destination failures,
and newest published event time.

Procedure: open Monitoring hub, filter to item/status/time, capture the run ID,
then drill into pipeline Copy details, Eventstream graph, Eventhouse ingestion,
or Spark progress. Compare with source controls and target counts rather than
reading “Succeeded” in isolation. A run identity needs access to monitoring and
the item; sensitive payloads should not be copied into broadly accessible logs.
Retain enough history to compare the same hour/day and detect gradual drift.

**Worked incident.** A pipeline reports success and copied one million rows, but
the source control total is 1.05 million. The watermark advanced. Evidence shows
50,000 conversion rejects that the job treated as tolerated. Operational success
is green; completeness is red. Freeze or correct the watermark according to the
replay design, repair the mapping, replay the bounded interval, reconcile, and
add a reject-rate alert. Do not rerun the entire source blindly.

Troubleshoot freshness by finding the oldest boundary that is late: source
availability, trigger/start queue, extraction, transfer, transform, target
commit, or consumer publish. Mini-lab: create a run record with read/written/
rejected counts and watermark; inject one missing file and one slow destination;
show which metrics distinguish completeness failure from throughput failure.

## Transformation monitoring field guide

<!-- block-id: monitor-transformation-comprehensive -->
A transformation is healthy only when code ran, output meets its contract, and
resource cost remains acceptable. For Dataflow Gen2, examine refresh start,
status, duration, submitter/capacity, failing query/step, rows or bytes where
reported, detailed logs, and destination results. For notebooks/Spark jobs,
examine application, stage and task distribution, shuffle/spill/skew, executor
loss, input/output, and assertions. For SQL/KQL, retain query/request ID,
duration, scanned data, queue/resource evidence, plan/query context, and result
validation.

Attach a quality result table to every curated output:

```text
run_id | dataset | rule_id | severity | evaluated | failed | threshold | disposition
```

Rules include schema, uniqueness, required values, range/domain, referential
integrity, timeliness, and reconciliation. Use a warning only when the documented
disposition allows publish; otherwise fail before replacing the last known-good
output. Protect quality samples because they may contain sensitive values.

**Scenario.** A Dataflow duration doubles but output counts remain correct. Drill
into source scan/bytes and folding evidence, destination write, gateway, and
capacity rather than treating it as data corruption. A notebook whose median
task is 20 seconds but one task is 12 minutes suggests skew; adding executors
may not fix one oversized partition. Mini-lab: set an allowed null-rate threshold,
run one pass below it and one above it, and verify publish, evidence, and alert
behavior match the declared severity.

## Semantic-model refresh field guide

<!-- block-id: monitor-semantic-comprehensive -->
Refresh monitoring begins with refresh history for the model and refresh
summaries for administrative scope where authorized. Capture model/workspace,
refresh ID or time, trigger type, status, start/end/duration, table/partition
detail, error, gateway/connection context, and capacity evidence. Distinguish
full, incremental/partition, and metadata-only behaviors as applicable. The
refreshing identity needs model and source/connection rights; broad workspace
Admin is not the default repair.

Trace consumer freshness backward. A model can refresh successfully from a
stale warehouse, so compare the upstream published watermark with the model's
source boundary and a consumer-visible maximum business timestamp. Incremental
refresh must include the intended partitions and handle late changes according
to policy. A renamed source column is deterministic and should be repaired; a
temporary gateway or capacity fault may justify bounded retry.

**Worked incident.** The 06:30 model refresh succeeds, but the dashboard still
shows yesterday. Refresh detail confirms every partition completed. The
warehouse publish watermark is also yesterday because upstream ingestion missed
its cutoff. The correct alert is end-to-end freshness, not another semantic
refresh. Mini-lab: document a source → lakehouse → warehouse → semantic model
chain, deliberately stale one boundary, and prove which timestamp identifies
the first stale stage.

For long refreshes, compare historical duration, table/partition time, source
query, gateway, capacity throttling, model size, and concurrent operations. For
failure, preserve the exact message and refresh context before retry. Validate
both failure and recovery; an alert that never resolves creates permanent noise.

## Alert engineering field guide

<!-- block-id: alerts-comprehensive -->
An alert contract contains signal and unit, scope, threshold, evaluation window,
minimum duration/consecutive evaluations, schedule, severity, owner, delivery
channel or action, deduplication key, suppression/cooldown, recovery condition,
and runbook. Use Activator where its event/condition/action model fits; use
workspace monitoring queries plus supported alert/action mechanisms where
log-derived conditions are required. Recipients need access to enough context to
act, but alerts should not disclose credentials or raw sensitive records.

Choose symptoms close to user impact: missed freshness cutoff, sustained lag,
failed required refresh, or quality threshold. Pair them with diagnostic signals
but avoid paging on every retry. Static thresholds fit contractual cutoffs;
rate-of-change or historical baselines fit gradual deviations. Route warning and
critical differently. Require acknowledgment/escalation for critical alerts and
define maintenance suppression.

**Worked alert.** Evaluate every five minutes: if consumer freshness lag exceeds
30 minutes for two consecutive evaluations, create one incident keyed by
dataset, notify the data-operations group, attach newest source and publish
timestamps plus last run ID, and link the freshness runbook. Recover only after
lag is below 15 minutes for two evaluations. This hysteresis prevents flapping.
Test with synthetic late data, verify exactly one firing, inspect the action,
restore freshness, and verify recovery.

If an alert does not fire, check signal production, time field/window, condition,
enabled state, permissions, action connection, and suppression. If it fires too
often, compare raw values and evaluation history before raising the threshold.
Mini-lab: design one failed-run alert and one freshness alert for the same
pipeline; explain why they can legitimately disagree.

<!-- block-id: monitoring-exam-distinctions -->
Monitoring hub centralizes supported job status; item views expose engine detail;
workspace monitoring stores supported log-level evidence; Capacity Metrics
explains CU use and throttling; Purview Audit records user/admin activity;
OneLake diagnostics records data access. “Succeeded” is execution evidence,
freshness is outcome evidence, and retry is a response only to a classified
transient fault.

<!-- block-id: monitoring-recall-lab -->
**Recall.** What equation detects silently rejected ingestion rows? Why can a
semantic refresh succeed while a dashboard is stale? Which metrics distinguish
Spark skew from general capacity pressure? What fields make a quality assertion
auditable? Why use hysteresis for recovery? For practice, write one outcome,
execution, and resource signal for pipeline, Dataflow, notebook, Eventstream,
and semantic model; identify the authoritative screen/log for each.

## Monitoring scenario drills

### Green run, stale consumer

The latest pipeline and semantic-model refresh both succeeded, but the dashboard
is four hours stale. Compare newest business timestamp at source, committed
ingestion watermark, curated publish timestamp, refresh source boundary, and
consumer-visible maximum. The first boundary that stops advancing owns the
initial investigation. A green downstream job may have consumed stale upstream
data correctly.

Alert on end-to-end freshness by dataset and cutoff, while retaining failed-run
alerts for execution diagnosis. Include last run IDs and stage timestamps. This
pair distinguishes “job failed” from “no fresh data arrived.”

### Rising stream lag with no failures

Input increases from 5,000 to 12,000 events/sec; output remains 7,000 and lag
grows. Examine boundary rates, micro-batch duration, state/shuffle, destination
latency, Eventhouse ingestion, and capacity. The absence of a red status does not
mean the service objective is healthy. Estimate time to exhaust backlog under
current rates and trigger before consumer freshness breaches.

After tuning or scaling, verify output eventually exceeds input long enough to
drain backlog, no events were dropped, and cost remains acceptable. Recovery is
not merely the moment input falls.

### Dataflow regression after a source release

Refresh duration triples immediately after a source deployment. Output remains
correct. Compare folding indicators/native query, source rows/bytes, gateway
route, query steps, destination metrics, and capacity. A new source view or type
can prevent folding without generating an error.

Record baseline and changed source/code versions. Repair foldability or move
selective operations earlier, then compare equivalent loads. Add a duration or
scan-volume anomaly alert only after understanding expected variation.

### Alert fires but nobody can act

An email says “pipeline failed” with no workspace, item, run ID, owner, or
runbook. The signal is technically correct and operationally weak. Redesign it
with dataset/item, environment, severity, failure/freshness context, correlation
ID, first diagnostic link, owner group, escalation, suppression key, and recovery
condition. Keep sensitive parameters and payloads out.

Test delivery during staffed and after-hours paths, duplicate failure retries,
maintenance suppression, and recovery. An alert is complete only when the
intended responder can locate and classify the incident.

## Capstone: the 06:00 operations review

You are the on-call analytics engineer. Executives expect the sales dashboard by
06:00. The chain is source close → pipeline ingestion → Dataflow cleanup → Spark
enrichment → warehouse publish → semantic refresh. Shipment events supply a
separate live tile. Build a five-minute review that finds risk before the user
does.

### Review order

Start with the outcome: newest consumer-visible sales business date/time and
live shipment lag. Compare each with its service objective. Then inspect the
stage boundary timestamps and committed watermarks. Only after locating the
first stale boundary drill into execution and resource evidence. This prevents
spending the whole review on one slow but noncritical activity.

Use Monitoring hub for supported run overview; pipeline/activity detail for
resolved runs and copy metrics; Dataflow refresh history/logs for query and
destination; Spark application/UI for stages and skew; warehouse query/monitor
for publish; semantic refresh history/summary for tables and partitions;
Eventstream/Eventhouse monitoring for rate, lag, invalid events, ingestion and
queries; and Capacity Metrics for shared throttling/CU context.

### Morning evidence board

Record a small operational table:

```text
dataset | source_ready | ingested_to | curated_to | model_to | consumer_to
        | status | run_id | rejects | freshness_lag | owner
```

For streaming add input rate, output rate, backlog/lag, late/invalid count, and
destination. For quality add evaluated and failed per critical rule. This table
contains references and aggregates, not raw sensitive payloads.

### Three observations

1. Sales ingestion succeeded to 05:40, Dataflow succeeded, but semantic model is
   at 04:00. Refresh detail shows incremental partitions excluded the newest
   boundary. Correct refresh policy/partition and retest; do not rerun ingestion.
2. Shipment input is 9,000/sec and output 6,000/sec with rising lag, no failure.
   Inspect operator/destination and capacity; alert on sustained lag because
   status alone is green.
3. Customer rejects rise from 0.02% to 4% after a source release. Stop publish
   under the quality contract, preserve last known-good output, investigate
   schema/type change, and communicate freshness impact.

### Alerts and handoff

Create distinct alerts for missed freshness cutoff, required job failure,
critical quality breach, sustained stream lag, and capacity throttling. Each
contains environment, dataset/item, current/threshold value, time window,
run/request ID, owner and runbook, deduplication, escalation, and recovery.
Suppress maintenance deliberately, not by muting broad channels.

The review is successful when it identifies the first stale/failing boundary,
distinguishes outcome from execution and resource, preserves correlation IDs,
routes to an accountable owner, and verifies recovery at the consumer. A ticket
closed after rerun is insufficient if the source-to-consumer timestamp or
quality control remains wrong.

## Exam distinctions

- Monitoring hub gives centralized visibility; item detail provides engine-specific evidence.
- Execution success is not data-quality success.
- Audit logs record user activities; monitoring logs record workload execution; OneLake diagnostics records access events.
- Alerts notify or act on conditions; they do not diagnose root cause automatically.
- Refresh history describes the semantic-model operation, not whether upstream data is complete.

## Active recall

1. Which metric proves consumer-visible freshness better than last run status?
2. Why compare rows read, written, and rejected?
3. Where do you begin for a cross-workspace job view?
4. Which semantic refresh failures should not be retried unchanged?
5. What makes an alert actionable instead of noisy?

## Authoritative sources

- [Use the Monitoring hub](https://learn.microsoft.com/en-us/fabric/admin/monitoring-hub)
- [Monitor Dataflow Gen2 refreshes](https://learn.microsoft.com/en-us/fabric/data-factory/dataflows-gen2-monitor)
- [Refresh summaries](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-summaries)
- [What is Fabric Activator?](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
