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
