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

## Streaming architecture decisions

<!-- block-id: streaming-engine-comprehensive -->
Select an engine by answering where events enter, where durable state lives,
what transformations require, and how results are served. Eventstreams provides
connector-driven ingestion, visual transformations, routing, and derived
streams. Eventhouse stores/indexes high-rate events and serves KQL. Spark
Structured Streaming provides code-first stateful processing over supported
sources and Delta sinks. Pipelines can deploy, schedule bounded reconciliation,
or coordinate companion jobs; they do not continuously evaluate each event.

Prerequisites include source authorization, destination write access, capacity,
network reachability, schema and event-time contract, retention, and an
operational owner. Prefer Eventstreams for accessible routing and straightforward
stream transforms; Eventhouse/KQL for low-latency log and time-series serving;
Spark for custom libraries, complex state, and Delta-centric engineering. A
combined design can route raw events through Eventstreams to Eventhouse for live
operations and OneLake/Delta for durable replay and Spark enrichment.

**Scenario.** Correlating device events across 30 minutes with a custom model
points to Spark; filtering and routing by device type without code points to
Eventstreams; ad hoc “last 15 minutes by firmware” queries point to Eventhouse.
Diagnose the architecture by measuring end-to-end latency, input/processing
rate, state growth, query concurrency, retention, and operator skill—not by
asking which product is newest. Mini-lab: draw two valid architectures for the
same stream, one low-code and one code-first, and identify recovery state,
serving store, and reconciliation in each.

## Native tables, shortcuts, and acceleration

<!-- block-id: native-shortcut-comprehensive -->
A native Eventhouse table ingests records into Eventhouse-controlled indexed
storage. It supports predictable KQL query performance and native policies at
the cost of ingestion, retention, and another representation. A OneLake
shortcut exposes supported Delta data as an external table without copying it;
query performance and availability depend on file layout, source, and external-
table support. Verify Delta format, schema, source permission/connection, and
the exact KQL access syntax before selecting a shortcut.

Choose native when continuous high-rate ingestion, low-latency concurrent KQL,
and native table features dominate. Choose a standard shortcut for historical
or shared open Delta data when avoiding movement matters and direct-read
performance is acceptable. If external queries are empty or fail, check target
path, `_delta_log`, schema compatibility, connection identity, source ACL,
partition/file health, and whether the query uses the external table correctly.
Mini-lab: query the same small Delta table through a shortcut and a native copy;
compare freshness boundary, features, rows scanned, latency, and ownership.

<!-- block-id: acceleration-comprehensive -->
Query acceleration adds an optimized cache for a configured recent period of a
OneLake shortcut. Choose the period from observed query predicates—for example,
seven days when most dashboards read seven days—not from total source retention.
Enable it on a supported shortcut, allow cache population, and inspect the
documented status/metrics before measuring warm and cold queries. Account for
premium cache/storage use, refresh lag, schema evolution, and external-table
feature limits.

Acceleration is preferable when a hot recent slice is repeatedly queried or
joined with native live data and the measured benefit justifies cost. Standard
shortcut remains preferable for infrequent, broad, or cost-sensitive access.
Native ingestion remains preferable when update policies, materialized views,
or other unsupported external-table features are required. For poor performance,
verify predicate time range overlaps the cache period, cache readiness, schema,
file layout, capacity, and query shape. Mini-lab: measure a 24-hour and 90-day
query before and after a seven-day cache; explain why only one should materially
benefit.

## Eventstream implementation

<!-- block-id: eventstreams-comprehensive -->
Define source schema, stable event ID, event-time field, units, expected rate,
and bad-event disposition. Create and authenticate the source, preview events,
normalize fields and types, filter unnecessary events early, then add derived
streams for reusable branches. Use group/aggregate and window operations only
after choosing event time and lateness behavior. Route raw, curated, and poison
branches to independently governed destinations. Validate one known event along
every intended route and monitor input, output, dropped/invalid events, latency,
and destination status.

**Worked route.** An IoT source branches raw events to a durable lakehouse,
valid temperature readings to Eventhouse, and invalid schema or out-of-range
values to a restricted quarantine destination with reason metadata. A derived
stream calculates five-minute device averages. Do not discard raw data merely
because the visual transform works; retained source events support replay after
logic changes. If output stops, walk source connection → incoming rate → each
operator's schema/output → route condition → destination connection/capacity.
Mini-lab: inject a valid event, wrong type, duplicate ID, late timestamp, and
out-of-range value and predict every branch before observing it.

## Structured Streaming implementation

<!-- block-id: spark-streaming-comprehensive -->
A Structured Streaming query has a logical plan, trigger/micro-batch execution,
state store when needed, sink, and checkpoint. Give each deployed query a
stable unique checkpoint path and protect it like operational state. Use
explicit schema for production inputs. Add event-time watermark before bounded
deduplication or stateful aggregation, choose an output mode supported by the
operation/sink, and write to a transactional Delta target. Monitor query progress
JSON, batch duration, input/processed rows per second, state rows/bytes, and sink
commit failures.

`foreachBatch` receives a DataFrame plus `batch_id` and is useful for `MERGE` or
multi-target batch logic. Make the body idempotent using `batch_id` control or
stable business/event keys; a failed micro-batch can be retried. Avoid calling
unbounded actions repeatedly, reusing a checkpoint for a changed incompatible
query, or placing checkpoints in temporary locations. If recovery fails, retain
the old checkpoint and source offsets, determine whether the query/state schema
changed, and create a controlled replay to a validated target rather than
deleting state and hoping.

**Mini-lab.** Run two micro-batches containing a duplicate ID and a late event,
stop gracefully, restart from the same checkpoint, and prove no logical output
duplicates. Then point a test copy at a fresh checkpoint and observe replay.
Compare append, update, and complete output semantics for one windowed count.
If processing falls behind, use progress metrics and Spark UI to distinguish
source rate, shuffle/state, skew, sink latency, and capacity.

## KQL transformation implementation

<!-- block-id: kql-comprehensive -->
KQL reads as an operator pipeline. Start from the smallest time/data scope;
`where` early, `project` required columns, parse dynamic JSON only where needed,
`extend` derived fields, and `summarize` at the declared grain. Use `join` with
the smaller side and a time/key bound, and use `materialize()` only when one
bounded intermediate is reused and measurement supports caching it. Retain a
request ID and inspect diagnostics for failed or slow queries.

```kusto
DeviceEvents
| where EventTime between (ago(30m) .. now())
| where isnotempty(DeviceId)
| extend Payload = todynamic(RawPayload)
| extend Temperature = todouble(Payload.temperature)
| where isnotnull(Temperature)
| summarize Events=count(), AvgTemp=avg(Temperature),
            P95=percentile(Temperature, 95)
    by DeviceId, bin(EventTime, 5m)
```

Validate input count, parse failures, filtered count, distinct devices, and
bucket totals. KQL null/empty and dynamic conversion rules deserve explicit
tests. An empty result may be correct because of time range or ingestion delay;
check table, database, time field, time zone, ingestion status, and filters
before changing syntax. Mini-lab: add malformed JSON, null temperature, and one
event outside the range; predict which metric accounts for each exclusion.

## Windowing implementation

<!-- block-id: windows-comprehensive -->
A tumbling window of width five minutes assigns each event to one nonoverlapping
bucket. A hopping window of width ten minutes and hop two minutes assigns one
event to up to five overlapping windows. A session window groups events for one
key until an inactivity gap closes the session. Sliding is sometimes used
conceptually for continuously moving boundaries; verify the engine's exact
operator terminology. Window choice follows the question: accounting totals
often tumble, moving signals hop, and user/device visits use sessions.

Suppose events for device A occur at 10:01, 10:04, 10:06, and 10:20. Five-minute
tumbling windows place the first two together and 10:06 separately. A session
gap of five minutes groups 10:01/10:04/10:06 and starts a new session at 10:20.
A 10-minute hopping window every five minutes can count an event in two outputs.
This overlap is expected, so summing hopping-window outputs again usually
double-counts.

Use event time for business windows, define time zone, establish watermark from
lateness evidence, and specify correction policy after finalization. A longer
watermark retains state and delays append-final output; a short watermark drops
or excludes more late data. Diagnose missing window counts through event-time
parse, watermark, window boundaries, time zone, late metrics, checkpoint state,
and output mode. Mini-lab: hand-calculate the four events above for tumbling,
hopping, and session windows, then add one event arriving 12 minutes late under
a 10-minute watermark.

<!-- block-id: streaming-exam-distinctions -->
Native tables ingest/index; standard shortcuts read Delta in place; accelerated
shortcuts cache a recent external slice but retain external-table limitations.
Eventstreams shape/route, Spark executes custom stateful code, KQL queries and
analyzes event stores, and Activator takes actions from conditions. Event time
drives business windows; processing time measures observation. Watermark bounds
lateness/state; checkpoint supports recovery; neither alone makes a sink
idempotent.

<!-- block-id: streaming-recall-lab -->
**Recall.** When is a native Eventhouse table worth another representation? Why
can a seven-day acceleration cache fail to help a 90-day query? What must every
Eventstream poison route retain? Why is each Spark query's checkpoint unique?
How can a KQL query distinguish parse failures from filtered values? How many
10-minute windows with a two-minute hop can contain one event? Build a one-page
operational contract listing event ID, event time, allowed lateness, checkpoint,
raw retention, sink key, replay method, metrics, and owner.

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
