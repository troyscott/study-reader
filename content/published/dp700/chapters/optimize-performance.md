# Optimize performance

<!-- block-id: orientation -->
Optimization is a measured loop: define the workload and target, capture a baseline, locate the bottleneck, change one relevant mechanism, and compare correctness, latency, throughput, and capacity cost. More compute is a hypothesis—not a diagnosis.

## Objective coverage

| Measured objective | Primary levers |
| --- | --- |
| Optimize a Lakehouse table | Delta file size, compaction, V-Order, partitioning, statistics, and maintenance |
| Optimize a pipeline | Copy parallelism, incremental selection, concurrency, staging, and orchestration overhead |
| Optimize a data warehouse | Distribution/scan reduction, statistics, query plans, concurrency, and table design |
| Optimize Eventstreams and Eventhouses | Early filtering, routing, ingestion batching, retention/cache, KQL shape, and materialization |
| Optimize Spark performance | Partitioning, pruning, shuffle, skew, caching, join strategy, and compute sizing |
| Optimize query performance | Filter/project early, minimize scanned data, inspect plans, and precompute repeated work |

## Optimize a Lakehouse table

Delta tables can accumulate many small Parquet files, increasing listing, metadata, and task overhead. `OPTIMIZE` compacts files; V-Order reorganizes Parquet encoding for Fabric read engines. They address file layout, not incorrect partitioning or poor queries.

```sql
OPTIMIZE lakehouse.sales_order
VORDER;
```

Partition only on columns that support frequent selective pruning and do not create extreme cardinality or tiny partitions. Date is often useful; customer ID often creates too many directories. Compact after meaningful write accumulation, not after every tiny batch. Retain files according to recovery/time-travel and governance requirements before vacuuming obsolete data.

## Optimize a pipeline

Measure source read, transfer, sink write, activity queue, and orchestration time separately. Select only changed rows/files and needed columns. Tune Copy Activity parallelism against source, network, capacity, and destination limits; maximum parallelism can trigger throttling and reduce total throughput.

Avoid thousands of tiny activities when one parameterized or batched operation can do the work. Use bounded ForEach concurrency. Stage only when it enables a required connector path or proven bulk-load benefit. Keep retries exponential and limited so a failing dependency does not multiply load.

## Optimize a data warehouse

Start with actual workload evidence: duration, scans, data movement, queuing, blocking, and execution plan. Use appropriate data types and a star schema, keep statistics current where applicable, filter early, avoid `SELECT *`, and precompute stable expensive logic when justified.

| Symptom | Investigate before scaling |
| --- | --- |
| Large scans | Predicate selectivity, column projection, table organization, statistics |
| Join explosion | Grain, duplicate keys, join cardinality, preaggregation |
| High concurrency latency | Queuing, workload shape, repeated scans, capacity saturation |
| One query regressed | Plan/data-distribution change, statistics, parameter sensitivity |

V-Order improves file organization for reads; it does not replace sound SQL, statistics, or relational design.

## Optimize Eventstreams and Eventhouses

In Eventstreams, filter and project early, avoid needless transformations on branches, route only required events, and monitor input/output/lag at each destination. Batch and schema choices affect destination ingestion efficiency.

In Eventhouse, set retention for business need and caching for the hot query horizon. In KQL, put selective `where` predicates early, constrain time, select needed columns, prefer term-aware string operators, and reduce both sides before large joins. Use materialized views or update policies for repeated transformations only when their ingestion cost and maintenance semantics are justified.

For OneLake shortcuts, compare standard access, query acceleration, and native ingestion. Acceleration is attractive for a recent hot window; native tables are better when native policies and consistently low latency are required.

## Optimize Spark performance

Spark performance is dominated by data scanned, partition count/size, shuffle, skew, serialization, and compute utilization.

1. Use the Spark UI to locate the slow stage and inspect task distribution, input, shuffle, spill, and failures.
2. Filter and project before wide transformations.
3. Avoid Python UDFs when built-in Spark functions express the operation.
4. Broadcast only genuinely small join inputs; otherwise choose partitioning that reduces movement.
5. Repartition deliberately before a large join/write; coalesce mainly to reduce partitions without a full shuffle.
6. Cache only reused, expensive intermediate data and unpersist it afterward.
7. Address skew through better keys, preaggregation, adaptive execution, or selective salting before adding executors.

```python
from pyspark.sql import functions as F

recent = orders.select("CustomerKey", "OrderDate", "Amount").filter(
    F.col("OrderDate") >= F.lit("2026-01-01")
)

result = recent.join(F.broadcast(customer_region), "CustomerKey")
```

The broadcast is appropriate only if `customer_region` is small enough for each executor. Confirm with plan and runtime evidence.

## Optimize query performance

Across SQL, KQL, and Spark SQL, the durable principles are similar:

- reduce rows and columns early;
- use predicates that enable pruning and indexes/statistics where supported;
- avoid repeated parsing, conversion, and computation;
- join at compatible grain and reduce before joining;
- preaggregate/materialize repeated expensive results when freshness permits;
- inspect the engine's actual plan and runtime metrics.

Optimization must preserve correctness. Compare row counts, totals, null behavior, and representative results after a rewrite. Report both latency and capacity/resource change so a faster query that costs far more is visible as a trade-off.

## The optimization experiment contract

<!-- block-id: optimization-foundation -->
Write the experiment before changing the system: workload/query/data version,
concurrency and cache state, environment/capacity, baseline runs, metric target,
correctness assertions, proposed bottleneck, one change, repeated result, and
cost/resource comparison. Use median and a tail percentile when variability
matters; one warm run after a cold baseline is not evidence. Preserve query/run
IDs and actual plans or engine metrics.

Optimize the dominant bottleneck. If time is source I/O, adding pipeline
activities can hurt. If one Spark partition is skewed, adding executors leaves
one long task. If capacity throttles many workloads, a local SQL rewrite may not
explain all latency. Scaling is valid when measured demand genuinely exceeds
available resources after reasonable efficiency work, but it proves only that
more resources helped that tested workload.

## Lakehouse optimization field guide

<!-- block-id: optimize-lakehouse-comprehensive -->
Inspect table size, file count and size distribution, partition columns/count,
write cadence, query predicates, bytes/files scanned, and Delta history before
maintenance. Many tiny files create metadata and task overhead. `OPTIMIZE`
compacts eligible files; V-Order reorganizes Parquet for Fabric read efficiency.
Partitioning creates directory-level pruning boundaries. These mechanisms solve
different problems and can be combined deliberately.

Choose low-cardinality, frequently filtered columns with balanced volume for
partitioning—often date at an appropriate grain. High-cardinality customer or
transaction IDs produce tiny partitions. Use optimized write/maintenance based
on accumulated data and query SLA, not after every micro-batch. Maintain
statistics where the engine uses them. Before `VACUUM`, confirm time-travel,
concurrent-reader, replay, legal retention, and recovery requirements; removed
files cannot support old versions.

**Lab.** Write the same representative table as thousands of tiny files and as
compacted files. Run identical selective and broad queries three times under
documented cache state; record planning/tasks, files/bytes, duration, and CU or
compute evidence. Apply `OPTIMIZE`/V-Order as supported and compare. Then test a
date partition versus an intentionally bad high-cardinality partition. Validate
row count, distinct key, and totals after every layout change.

If optimization appears ineffective, verify the query actually reads the
optimized table/version, predicate can prune, file accumulation warranted
compaction, and competing capacity/cache conditions are comparable. V-Order
does not repair skewed partitioning, nonselective queries, or incorrect data
modeling.

## Pipeline optimization field guide

<!-- block-id: optimize-pipeline-comprehensive -->
Break elapsed time into trigger/queue, orchestration overhead, source query,
transfer, transform, staging, sink write/commit, and retry. Capture rows/bytes,
throughput, parallel copies, ForEach concurrency, source and sink utilization,
throttling, file counts, and capacity. First reduce work with incremental
selection, partition pruning, column projection, and compression. Then tune
parallelism within source, gateway/network, Fabric capacity, and sink limits.

Copy parallelism controls work within a copy; ForEach concurrency controls
simultaneous activities. Raising both multiplies pressure. Many tiny activities
increase scheduling and connection overhead, while one giant serial copy may
underutilize resources. Partition/batch at recoverable boundaries. Use staging
only when a connector path or measured bulk-loading improvement warrants its
extra I/O. Backoff protects a throttled dependency; instant high retry amplifies
the outage.

**Lab.** Copy 20 equally sized partitions at concurrency 1, 4, and 12 while
recording total throughput, source/sink throttling, activity duration, and
capacity. Keep mapping and data fixed. The best point is the lowest reliable
resource cost meeting SLA, not automatically 12. Repeat with 2,000 tiny files
versus consolidated inputs to expose orchestration/file overhead. Validate
source-to-target counts and repeat-safe rerun.

If throughput falls as concurrency rises, inspect source connection limits,
gateway/network, sink commits/locks, capacity, and generated small files. If
queue time dominates, inspect capacity and activity count. If one partition
dominates, rebalance boundaries rather than globally increasing parallelism.

## Warehouse optimization field guide

<!-- block-id: optimize-warehouse-comprehensive -->
Begin with Query insights/monitor, actual plan and runtime metrics, query text
and parameters, data volume/distribution, statistics, concurrency, and Capacity
Metrics. Classify scan, join/data movement, sort/aggregate, blocking, queueing,
spill, or compilation/plan change. Select only required columns, use types that
represent values without needless width, filter with sargable/selective
predicates, preaggregate before many-to-many joins, and preserve a clean star
grain.

Statistics help estimates; stale or absent statistics can lead to a poor join
order or movement. Materialized views or persisted curated tables can trade
refresh/storage cost for repeated query savings. Avoid wrapping a filter column
in a conversion when the same boundary can be expressed on the original type.
Avoid `SELECT *`, accidental Cartesian joins, and row-by-row procedural logic.
Capacity scale can help concurrency saturation but not a query that scans every
wide row unnecessarily.

**Lab.** Start with a query joining order facts to a dimension whose business
key is duplicated. Capture the wrong row count and plan. Repair dimension
uniqueness, project only required columns, add a selective date predicate, and
compare scan, duration, and correct total. Next preaggregate facts before a
consumer-level join and compare. Run at one and several concurrent users so a
single-query gain is not mistaken for workload capacity.

For regressions, compare code/data/statistics/plan/concurrency/capacity changes.
If all queries slow, suspect shared resource or blocking before rewriting each.
If only one parameter shape slows, investigate selectivity and plan behavior.
Do not “optimize” by removing correctness filters or changing decimal semantics.

## Real-Time Intelligence optimization field guide

<!-- block-id: optimize-realtime-comprehensive -->
For Eventstreams, measure source input, operator/branch output, processing lag,
invalid/drop rate, and each destination. Filter and project early, avoid
duplicating expensive transforms on every branch, and route only required
events. Choose batching and destinations with end-to-end latency in mind; one
slow destination must be identifiable rather than silently backing up every
route.

For Eventhouse, compare ingestion rate/batch metrics, hot-cache horizon,
retention, storage, query logs/insights, scanned extents/data, concurrency, and
capacity. Put time and selective `where` early, `project` needed columns, use
term-aware operators, reduce both sides before joins, and avoid repeatedly
parsing broad dynamic payloads. Set caching to the frequently queried hot
horizon and retention to the business/governance horizon; they answer different
questions.

Use materialized views for frequently repeated aggregates when ingestion-time
maintenance and freshness semantics are acceptable. Use update policies for
supported deterministic derived ingestion when duplicated storage and failure
behavior are understood. For external Delta, compare standard shortcut,
accelerated recent window, and native ingestion; acceleration does not unlock
all native-table features.

**Lab.** Query 90 days when most users need 24 hours. Add an explicit time
predicate and projection, measure scanned data and latency, then configure a hot
cache/accelerated period aligned to the observed horizon where appropriate.
Create a repeated five-minute aggregation and compare direct query with a
materialized design including ingestion cost. Validate bucket totals and late-
event behavior. If lag increases, localize source, operator, Eventhouse
ingestion, or query/capacity pressure before scaling.

## Spark optimization field guide

<!-- block-id: optimize-spark-comprehensive -->
Use Spark UI to identify the critical stage and its task distribution. Record
input/output rows and bytes, partitions, median/max task duration, shuffle read
and write, spill, skew, executor CPU/memory/GC, failures, and plan. Reduce scan
through partition pruning, column projection, and predicate pushdown. Prefer
built-in functions and vectorized execution to Python UDFs. Avoid unnecessary
wide transformations and repeated recomputation.

Broadcast a dimension only when its serialized size safely fits every executor
and the plan confirms broadcast. Otherwise align/repartition around large joins
carefully. `repartition` performs a shuffle to reshape/increase/decrease
partitions; `coalesce` typically reduces without full balancing. Address skew
with better keys, preaggregation, adaptive query execution, or selective
salting. Cache only an expensive reused intermediate that fits memory and
unpersist it; caching one-use data adds cost.

Size compute after the plan is efficient. More executors increase parallel
capacity but cannot split a single indivisible/skewed task automatically. A
larger driver helps driver duties but can hide an unsafe collect. Too many tiny
partitions add scheduling overhead; too few large partitions underuse compute
or spill. Match output partitioning/file sizes to downstream reads as well as
current job speed.

**Lab.** Create a skewed join and capture one long task. Compare baseline,
preaggregation, and selective salting/adaptive execution; record task spread,
shuffle, spill, duration, and totals. Separately compare a built-in expression
with an equivalent Python UDF and inspect the plan. Cache a reused intermediate
for two actions, then unpersist; prove a one-action workload does not benefit.

## Cross-engine query optimization field guide

<!-- block-id: optimize-query-comprehensive -->
The common model is scan → filter/project → join → aggregate/sort → return or
write. Reduce data as early as semantics permit, use engine-prunable predicates,
make join keys compatible, prevent many-to-many explosion, and calculate
expensive repeated results once. But verify the actual engine plan: SQL
statistics and relational operations, KQL extent/time pruning and operator
pipeline, and Spark partition/file pruning plus shuffle have different evidence.

Compare both cold and representative warm-cache conditions, several runs,
concurrency, result size, and capacity cost. A query can be faster because the
result changed, cache warmed, data volume shrank, or capacity was quieter. Use a
fixed correctness fixture plus production-scale measurement. Validate row count,
key uniqueness, null behavior, decimal/time-zone semantics, and totals before
accepting a rewrite.

**Worked comparison.** SQL `WHERE OrderDate >= @start`, KQL `where EventTime >=
start`, and Spark `.filter(col("OrderDate") >= start)` can all reduce scans only
when types, storage organization, and optimizer/source pushdown support it.
Wrapping the stored date in string conversion may prevent pruning. Preaggregate
a large fact by join key before joining to a small classification when only
group totals are needed—but never if detail-level matching changes meaning.

If a rewrite shows no gain, check plan equivalence, predicate selectivity,
storage/partitioning, statistics, cache, result transfer, and shared resource
noise. If it is faster but CU/resource cost rises sharply, state the trade-off
and decide against the SLA/cost objective. Mini-lab: build a result checksum and
metrics table, then optimize one SQL, KQL, and Spark query using the same
filter/project/join principles and engine-specific evidence.

<!-- block-id: optimize-exam-distinctions -->
`OPTIMIZE` compacts Delta files, V-Order changes file layout, partitioning enables
pruning, and `VACUUM` removes obsolete files under retention rules. Copy
parallelism differs from loop concurrency. Eventhouse retention differs from hot
cache. Spark repartition differs from coalesce, and broadcast is a join strategy,
not “send output everywhere.” A faster run is not proven optimization until
correctness, comparable conditions, and resource cost are included.

<!-- block-id: optimize-recall-lab -->
**Recall.** Which metrics prove a small-file problem? Why can 12 concurrent
copies be slower than four? What plan evidence distinguishes warehouse scan from
queueing? When does a materialized view move cost rather than remove it? Why does
one long Spark task suggest skew? How can conversion prevent pruning? For
practice, write an A/B optimization record with hypothesis, fixed conditions,
three baseline and three changed runs, correctness checksum, p50/p95, bytes
scanned, and CU/compute result.

## Optimization scenario drills

### Fast query, expensive capacity

A warehouse rewrite lowers median latency from 12 to 4 seconds but doubles CU
consumption and worsens p95 under concurrency. The change is not automatically
an improvement. Recheck result equivalence, scan/data movement, plan, repeated
work, and concurrency. Decide against the stated SLA and cost objective: perhaps
8 seconds at lower CU meets the business need and protects other workloads.

Report latency distribution and cost together. A local speedup that causes
capacity throttling can make the overall product slower. Optimization ownership
extends beyond the single developer's test query.

### Small files caused by streaming writes

A Delta table receives frequent tiny micro-batches and accumulates thousands of
small files per day. Queries spend substantial time listing/planning and launch
many tiny tasks. Measure file distribution and scan/task evidence, then choose a
maintenance cadence or optimized-write strategy that compacts after sufficient
accumulation without running `OPTIMIZE` after every batch.

Coordinate compaction, V-Order, readers, retention, and vacuum safety. Compare
end-to-end write plus maintenance cost with query benefit. If queries do not read
the table often, aggressive maintenance may cost more than it saves.

### Parallelism cliff

A Copy pipeline improves from concurrency 1 to 4, then slows at 16 while source
throttling and sink commit waits rise. Select the measured knee—perhaps 4 or 8—
and use backoff. Tune copy-internal parallelism and ForEach concurrency together
because their product determines pressure. Repartition source work so one giant
partition does not dominate.

Repeat across representative volume and time, since external source limits can
vary. Validate target counts and file layout; faster transfer that produces a
small-file problem moves the cost downstream.

### Broadcast assumption fails

A lookup table was small during development but grows to several gigabytes.
Forced broadcast now causes executor memory pressure and failures. Remove the
assumption or define a guarded size threshold, inspect the adaptive/actual plan,
and choose a partitioned join strategy. Project only required lookup columns and
filter it before considering broadcast.

Compare shuffle, spill, task distribution, executor memory, duration, and
correct totals. “Dimension” is a logical role, not proof that its physical size
is safe to copy to every executor.

### Materialization freshness trade-off

A KQL aggregation over raw events is run hundreds of times per hour. A
materialized view can shift repeated query computation to ingestion/maintenance,
but adds storage, update cost, and freshness/late-data semantics. Measure total
query savings against ingestion overhead and verify supported functions and
correction behavior.

If users require immediate raw detail and only a few queries use the aggregate,
direct query may be better. If the aggregate is stable and dominant, materialize
with monitoring for health and lag. Cost is moved and amortized, not magically
removed.

### Scaling after efficiency work

Capacity Metrics shows sustained throttling across well-designed concurrent
workloads after unnecessary scans, skew, retries, and schedules are addressed.
Scaling or autoscale is now an evidence-backed option. Define expected demand,
budget, success metric, and rollback; compare throttling, latency, throughput,
and CU/cost after the change.

Scaling is not a failure of engineering when demand exceeds the provisioned
resource. It is a poor first answer when one accidental Cartesian join or
unbounded stream state consumes the capacity.

## Capstone: optimize without moving the bottleneck

A Fabric product misses its 07:00 freshness objective. Pipeline elapsed time is
95 minutes, Spark transformation 40 minutes, warehouse publish 20 minutes, and
semantic refresh 25 minutes, but several stages overlap. Interactive reports
also slow during the load. The team proposes a larger capacity immediately.

### Establish the critical path

Create a timeline using trigger, queue, source extraction, Copy, Spark stages,
warehouse application, model refresh, and publish. Overlap means durations cannot
simply be added. Identify the earliest time each required output is ready and the
dependency that determines consumer readiness. Collect Capacity Metrics for
throttling and workload overlap, item run IDs, source/sink throughput, Spark UI,
warehouse query/plan, and refresh partition detail.

Set fixed correctness controls: selected source rows = accepted + rejected,
target distinct business keys, amount totals, late partition count, and
consumer-visible maximum business time. Record three comparable baseline days
and their cache/concurrency/capacity state.

### Competing hypotheses

Pipeline evidence shows 6,000 tiny files and source throttling at high copy
parallelism. Spark shows large file-list/task overhead plus one skewed customer
key. Warehouse publication scans the full fact table despite processing one day.
Semantic refresh unnecessarily processes historical partitions. Capacity also
shows brief throttling while all operations overlap.

These are four hypotheses, not one “Fabric is slow” diagnosis. Test in controlled
increments:

1. Reduce Copy/ForEach concurrency to the measured throughput knee and consolidate
   file boundaries, preserving restartable partitions.
2. Compact/optimize accumulated Delta layout at an evidence-based cadence and
   address Spark skew through preaggregation or a targeted strategy.
3. Make warehouse application and query predicates prune the bounded date range;
   update relevant statistics and inspect the changed plan.
4. Configure/validate semantic incremental partitions and schedule heavy stages
   to reduce unnecessary contention where business dependencies permit.

Do not apply every change at once. Each experiment retains input version,
configuration, p50/p95 or repeated duration, bytes/files/tasks/shuffle/scan,
capacity/CU, and correctness checksum.

### Interpret results

Suppose file consolidation cuts Spark planning/task overhead by 12 minutes;
skew repair removes a 9-minute tail; bounded warehouse processing saves 8
minutes; incremental semantic refresh saves 10. Scheduling reduces p95 report
latency during the load. End-to-end readiness improves by only 25 minutes because
some savings overlap. Report critical-path improvement, not the sum of local
speedups.

Capacity now shows no throttling on typical days but p95 seasonal days still
breach SLA. Model seasonal demand and compare further efficiency, schedule,
autoscale, or SKU change. Scaling is now evaluated against a residual measured
resource limit rather than masking small files, skew, full scans, and unnecessary
refresh.

### Regression and operations

Add thresholds for file-count/size distribution, Spark skew ratio and spill,
pipeline throughput/throttling, warehouse scan/plan regression, refresh duration,
capacity throttling, and end-to-end freshness. Avoid alerting on one noisy sample;
use appropriate windows and recovery. Maintenance jobs themselves consume
capacity, so schedule and measure compaction/materialization costs.

The capstone passes when the same source produces identical accepted/rejected
counts and business totals; the critical path meets the objective on repeated
representative runs; p95 interactive performance does not regress; capacity cost
is reported; every maintenance/scale decision has ownership and rollback; and a
future data-volume change can be detected before the original bottleneck returns.

## Exam distinctions

- `OPTIMIZE` compacts Delta files; V-Order changes Parquet layout; partitioning organizes data for pruning.
- Pipeline concurrency and Copy Activity parallelism are related but different controls.
- Cache hot Eventhouse data based on query horizon; retention controls how long data remains.
- Spark `repartition` shuffles to reshape partitions; `coalesce` normally reduces them with less movement.
- A broadcast join copies the small side to executors; it is harmful when the “small” side is not small.
- Scaling capacity can relieve saturation but does not repair unnecessary scans, skew, or bad grain.

## Active recall

1. Which symptoms indicate a small-file problem?
2. Why can more Copy Activity parallelism make a pipeline slower?
3. What evidence would justify a materialized view in Eventhouse?
4. Compare repartition and coalesce.
5. Why must optimization results include correctness and capacity cost?
6. A query sped up after scaling. What has—and has not—been proven?

## Authoritative sources

- [Lakehouse and Delta tables](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-and-delta-tables)
- [Delta optimization and V-Order](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order)
- [Warehouse performance guidelines](https://learn.microsoft.com/en-us/fabric/data-warehouse/guidelines-warehouse-performance)
- [Spark errors and performance troubleshooting](https://learn.microsoft.com/en-us/fabric/data-engineering/troubleshoot-spark)
- [KQL query best practices](https://learn.microsoft.com/en-us/kusto/query/best-practices)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
