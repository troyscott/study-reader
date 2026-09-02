# Ingest and transform streaming data

<!-- block-id: orientation -->
Streaming systems trade bounded batch simplicity for continuous state. Choose the engine from latency, event volume, transformation complexity, operational ownership, and serving/query needs; then make time and failure semantics explicit.

## Objective coverage

| Measured objective | What to master |
| --- | --- |
| Choose an appropriate streaming engine | Eventstreams, Eventhouse/KQL, Spark Structured Streaming, and pipeline boundaries |
| Choose between native tables and OneLake shortcuts in Real-Time Intelligence | Ingest/index versus query data in place |
| Choose between Query acceleration for OneLake shortcuts and standard OneLake shortcuts in Real-Time Intelligence | Cache window, performance, freshness, cost, and limitations |
| Process data by using Eventstreams | Sources, transformations, derived streams, routing, and destinations |
| Process data by using Spark structured streaming | Sources/sinks, checkpoints, output modes, watermarks, and state |
| Process data by using KQL | Filtering, parsing, summarizing, joining, and time-series operations |
| Create windowing functions | Tumbling, hopping/sliding, and session windows with event time |

## Choose an appropriate streaming engine

| Engine | Choose it for | Main trade-off |
| --- | --- | --- |
| Eventstreams | No-code/low-code ingestion, filtering, transformation, and routing | Less arbitrary code than Spark |
| Eventhouse and KQL | High-rate event storage and low-latency time-series/log queries | Optimized for event analytics rather than general ETL |
| Spark Structured Streaming | Code-first, complex/stateful processing with Delta integration | Greater engineering and state-management responsibility |
| Pipeline | Orchestrating bounded jobs around a stream | Not the continuous event-processing engine itself |

Use Eventstreams to connect and route; Eventhouse to retain and query time-oriented data; Spark when custom algorithms, libraries, or complex state are required. They can form one design rather than mutually exclusive choices.

## Choose between native tables and OneLake shortcuts in Real-Time Intelligence

A native Eventhouse table ingests data into Eventhouse-managed, indexed storage. It gives predictable KQL performance and supports table policies, at the cost of ingestion and another managed representation. A OneLake shortcut exposes Delta data as an external table through `external_table()` without moving it.

Choose native ingestion for consistently low-latency, high-concurrency event queries and Eventhouse policy features. Choose a standard shortcut when data already lives in OneLake/open storage, freshness through the source is acceptable, and avoiding movement matters more than native query speed.

## Choose between Query acceleration for OneLake shortcuts and standard OneLake shortcuts in Real-Time Intelligence

Query acceleration caches a configured recent period of shortcut Delta data and builds structures that approach native-table query performance. It is useful for hot recent data or joins between historical OneLake data and live Eventhouse events.

| Choice | Performance | Storage/cost | Constraints |
| --- | --- | --- | --- |
| Standard shortcut | Reads external Delta at query time | Avoids accelerated cache | Network/file layout and lack of indexes affect latency |
| Accelerated shortcut | Caches a time window for faster queries | Premium cache and indexing consume resources | External-table limitations remain; schema/policy constraints apply |

Set the cache period from the actual query horizon. Acceleration is not a full ingestion conversion: accelerated external tables still do not support every native-table feature, including documented materialized-view and update-policy scenarios.

## Process data by using Eventstreams

An Eventstream connects event sources, applies no-code operations, and sends results to one or more destinations. Typical operations include filtering, field management, aggregation, group-by, union, expansion, and content-based routing. A **derived stream** makes a transformed branch reusable.

Design steps:

1. Define event schema, ID, event-time field, and expected rate.
2. Select and secure the source connector.
3. Filter early and normalize types/names.
4. Apply windowed aggregation or routing only after time semantics are clear.
5. Route raw and curated branches to their respective destinations.
6. Monitor input, output, invalid events, lag, and destination errors.

## Process data by using Spark structured streaming

Spark treats a stream as an incrementally updated table. A durable checkpoint stores progress and state so a query can recover. Each production query needs its own stable checkpoint path; deleting or reusing it changes recovery semantics.

```python
from pyspark.sql import functions as F

events = spark.readStream.format("delta").table("bronze_events")

windowed = (
    events.withWatermark("event_time", "10 minutes")
    .dropDuplicatesWithinWatermark(["event_id"])
    .groupBy(F.window("event_time", "5 minutes"), "device_id")
    .agg(F.avg("temperature").alias("avg_temperature"))
)

(
    windowed.writeStream.format("delta")
    .outputMode("append")
    .option("checkpointLocation", "Files/checkpoints/device_5m")
    .toTable("silver_device_windows")
)
```

Output modes describe emitted results: append emits final new rows where supported, update emits changed rows, and complete emits the full result table. The sink must support the chosen mode. `foreachBatch` enables batch logic per micro-batch, but that logic must use the batch ID or stable keys to remain idempotent.

## Process data by using KQL

KQL is a pipeline language: each operator receives a tabular result and passes another result forward.

```kusto
DeviceEvents
| where EventTime > ago(1h)
| where isnotnull(Temperature)
| summarize AvgTemperature=avg(Temperature), Events=count()
    by DeviceId, bin(EventTime, 5m)
| where AvgTemperature > 80
| order by EventTime desc
```

Filter early, select only needed columns, parse dynamic fields deliberately, and use time-bounded joins. `summarize ... by bin()` forms fixed time buckets; time-series functions and materialized views serve repeated analytical patterns where supported.

## Create windowing functions

| Window | Behavior | Example use |
| --- | --- | --- |
| Tumbling | Fixed, nonoverlapping intervals | Five-minute totals |
| Hopping/sliding | Fixed width, starts more frequently than width | Ten-minute moving measure every minute |
| Session | Variable window closes after inactivity gap | User/device activity sessions |

Windows should use event time when results describe when events happened. A watermark states how late the engine expects events and bounds retained state; it does not reorder the entire infinite stream or guarantee that later records will be accepted.

## Exam distinctions

- Native Eventhouse tables ingest and index; shortcuts query supported data in place.
- Query acceleration caches a shortcut window but does not turn it into a fully native table.
- Event time describes occurrence; processing time describes observation by the engine.
- A watermark bounds late-data state; a checkpoint supports restart/recovery.
- Tumbling windows do not overlap; hopping windows can; session windows depend on inactivity.
- Eventstreams route/shape events; Activator evaluates conditions and takes actions.

## Active recall

1. Why might an accelerated shortcut still be the wrong choice for an update policy?
2. Which engine would you choose for custom stateful correlation, and why?
3. What happens when a checkpoint directory is discarded?
4. Compare a ten-minute tumbling window with a ten-minute window sliding every minute.
5. Why should a streaming join be time bounded?
6. Which metrics reveal backpressure or destination failure?

## Authoritative sources

- [Real-Time Intelligence overview](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/overview)
- [OneLake shortcuts in a KQL database](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/onelake-shortcuts)
- [Query acceleration overview](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/query-acceleration-overview)
- [Stateful processing with Structured Streaming](https://learn.microsoft.com/en-us/fabric/data-engineering/structured-streaming-stateful-processing)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
