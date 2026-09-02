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
- [KQL query best practices](https://learn.microsoft.com/en-us/kusto/query/best-practices)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
