# Ingest and transform batch data

<!-- block-id: orientation -->
Batch design begins with workload shape: data volume, latency, source ownership, transformation complexity, serving engine, and operational skill. The correct answer is rarely “use the newest feature”; it is the mechanism whose semantics fit the requirement.

## Objective coverage

| Measured objective | What to master |
| --- | --- |
| Choose an appropriate data store | Lakehouse, warehouse, Eventhouse, and operational-store fit |
| Choose between Dataflows Gen2, notebooks, KQL, and T-SQL for data transformation | User, engine, language, scale, and destination fit |
| Create and manage OneLake shortcuts | References, target/source behavior, credentials, schema, caching, and deletion |
| Implement mirroring | Database, metadata, and open mirroring; replication versus in-place access |
| Ingest data by using pipelines | Copy, parameters, staging, retries, and monitoring |
| Transform data by using PySpark, SQL, and KQL | Equivalent relational operations and engine-specific strengths |
| Denormalize data | Join normalized entities into a consumption-oriented shape |
| Group and aggregate data | Grain, grouping keys, measures, and null behavior |
| Handle duplicate, missing, and late-arriving data | Explicit quality rules, quarantine, correction, and observability |

## Choose an appropriate data store

| Store | Best fit | Key clue |
| --- | --- | --- |
| Lakehouse | Open files/Delta, Spark engineering, mixed structured data | Multiple engines need the same OneLake data |
| Warehouse | Governed relational analytics and T-SQL | Dimensional SQL serving and transactions dominate |
| Eventhouse | High-ingest, time-series/log analytics with KQL | Low-latency event exploration and time windows dominate |
| Operational database | Application transactions | Point writes and application consistency, not analytical scans |

Do not choose from language preference alone. Consider concurrency, update pattern, governance, latency, file/table format, and consumers.

## Choose between Dataflows Gen2, notebooks, KQL, and T-SQL for data transformation

**Dataflow Gen2** is Power Query-based, visual, and approachable for reusable tabular shaping. **Notebooks** provide PySpark/Python/SQL flexibility and distributed control. **T-SQL** fits set-based relational transformations close to a warehouse. **KQL** fits telemetry, logs, semi-structured events, and time-series analysis in Eventhouse.

### Dataflow Gen2 in depth

A useful Dataflow Gen2 review follows the data:

1. Connect and authenticate to a source.
2. Assign correct data types early; type drives comparison, arithmetic, and folding behavior.
3. Select/rename columns and filter rows to reduce unnecessary data.
4. Clean values: replace errors, trim/standardize text, handle nulls, and remove duplicates using an explicit key.
5. Combine data: **merge** performs a join; **append** stacks compatible rows.
6. Reshape: split/merge columns, pivot/unpivot, group, aggregate, and add derived columns.
7. Define destination and write behavior, then monitor refresh.

**Query folding** pushes supported transformations back to the source. Keep foldable filters and projections early, inspect folding indicators/query plans when available, and avoid assuming every connector or step folds. A nonfolding custom operation can force much more data into the mashup engine.

Schema strategy matters. Fixed destination schema gives predictable downstream contracts; automatic or dynamic handling eases evolution but can surprise consumers. Treat added columns, removed columns, type changes, and renamed columns as different events with explicit policy. Dataflow destinations and update methods vary, so verify whether append, replace, or another supported behavior matches the target.

Use Dataflow Gen2 for analyst-friendly transformations and managed destinations; use a notebook when logic needs libraries, tests, complex algorithms, or distributed tuning. Use SQL/KQL when the data already lives in the corresponding engine and set-based work can remain close to storage.

## Create and manage OneLake shortcuts

A shortcut is an independent OneLake object pointing to a target path. It avoids an extra copy and exposes supported external or internal data through the OneLake namespace. Deleting the shortcut does not delete the target; moving or deleting the target can break the shortcut.

Create table shortcuts in the lakehouse `Tables` area for supported table formats and file shortcuts in `Files`. Plan the cloud connection and credentials, source permissions, shortcut security, cache behavior, and schema evolution. The shortcut is read-through access, so source availability and network latency remain relevant.

## Implement mirroring

Mirroring adds a source database or catalog to Fabric. **Database mirroring** continuously replicates supported operational data into OneLake Delta tables. **Metadata mirroring** synchronizes catalog metadata and uses shortcuts to open-format data in place. **Open mirroring** accepts change files written to a Fabric landing zone according to the published specification.

Choose a shortcut for selected open-format tables/folders, mirroring for a database/catalog as a unit, and pipeline/copy when custom cadence, complex shaping, or a non-OneLake destination is needed. Mirrored tables are not general-purpose writable replicas; change the source and let synchronization propagate.

## Ingest data by using pipelines

Pipeline Copy Activity supports controlled movement across connectors and destinations. Parameterize dataset/path/table names, choose mappings deliberately, configure parallelism from measurements, and preserve source metadata. Use staging only when required by the connector or performance design.

Capture rows read/written/skipped, duration, throughput, run ID, watermark, and rejected records. Retry transient throttling or network faults with backoff; do not repeatedly retry invalid credentials or deterministic schema errors.

## Transform data by using PySpark, SQL, and KQL

These examples all aggregate valid sales by region, but they execute in different engines:

```python
from pyspark.sql import functions as F

result = (
    sales.filter(F.col("Amount").isNotNull())
    .groupBy("Region")
    .agg(F.sum("Amount").alias("Revenue"))
)
```

```sql
SELECT Region, SUM(Amount) AS Revenue
FROM dbo.Sales
WHERE Amount IS NOT NULL
GROUP BY Region;
```

```kusto
Sales
| where isnotnull(Amount)
| summarize Revenue = sum(Amount) by Region
```

PySpark favors distributed file/table processing, T-SQL relational warehouse workloads, and KQL event/time-series exploration. Equivalent syntax does not imply identical null, type, optimizer, or consistency behavior.

## Denormalize data

Denormalization joins entities into a consumption-oriented table to simplify queries and reduce repeated joins. First declare output grain, then select the correct one-to-one or many-to-one joins. A one-to-many join can multiply rows and measures; validate counts and key uniqueness before and after.

## Group and aggregate data

Grouping changes grain. Every nonaggregated output column must be a grouping key. Decide whether measures are additive, semi-additive, or nonadditive. `SUM(Amount)` can be additive; inventory snapshots should not be summed across time; ratios should normally be recomputed from numerator and denominator.

## Handle duplicate, missing, and late-arriving data

- **Duplicates:** define the business/event key, rank by trusted version/time, retain one winner, and record discarded rows.
- **Missing values:** distinguish unknown, not applicable, and invalid. Impute only with a defensible rule; otherwise quarantine or preserve null with a quality flag.
- **Late data:** use overlap windows and event/business time; reopen affected partitions or dimensions and restate downstream aggregates when policy requires it.

Quality handling must be observable. Track rule, count, sample, source, run, and disposition. Silently dropping bad rows makes a pipeline look successful while corrupting completeness.

## Exam distinctions

- Merge joins columns; append stacks rows.
- Shortcut references selected data; mirroring brings in a database/catalog and may replicate or reference depending on source.
- Query folding is source pushdown, not merely a successful Dataflow refresh.
- Grouping changes grain; denormalization can multiply rows if join cardinality is wrong.
- Tool choice follows workload and engine, not just which languages the engineer knows.

## Active recall

1. When does a shortcut beat a copy, and when does mirroring beat both?
2. What breaks query folding, and why does that matter?
3. Explain merge versus append in Power Query.
4. Why can a dimension join double a fact-table total?
5. Which records would you quarantine rather than impute?
6. Translate a SQL `GROUP BY` into KQL and PySpark.

## Authoritative sources

- [Dataflows Gen2 overview](https://learn.microsoft.com/en-us/fabric/data-factory/dataflows-gen2-overview)
- [Choose a data movement strategy](https://learn.microsoft.com/en-us/fabric/data-factory/decision-guide-data-movement)
- [OneLake shortcuts](https://learn.microsoft.com/en-us/fabric/onelake/onelake-shortcuts)
- [Mirroring overview](https://learn.microsoft.com/en-us/fabric/mirroring/overview)
- [Official DP-700 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700)
