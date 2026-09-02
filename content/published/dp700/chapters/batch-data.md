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

## Data-store decision workshop

<!-- block-id: batch-store-comprehensive -->
Choose the store from the dominant access and mutation pattern. A lakehouse keeps
Delta and files in OneLake for open, multi-engine engineering and analytics. A
warehouse provides a relational, governed T-SQL serving experience for
dimensional models and concurrent BI. An Eventhouse is designed for high-rate,
time-oriented ingestion and KQL exploration. An operational database owns
application transactions and point reads/writes; copying or mirroring its data
to an analytical store protects the application from scan-heavy workloads.

Prerequisites include the right Fabric capacity, workspace/item permissions,
source connectivity, and a retention/security design. Procedure: quantify data
volume and velocity, latency objective, update/delete frequency, transaction
needs, query language, concurrency, file-format interoperability, and consumers;
score each store; prototype the highest-risk query and load. A lakehouse is not
automatically fastest for every SQL dashboard, and a warehouse is not the right
landing zone for arbitrary binary files.

**Scenario.** A team receives Parquet telemetry plus curated sales dimensions.
Land and engineer open telemetry in a lakehouse, serve governed star-schema BI
from a warehouse when T-SQL concurrency dominates, and use Eventhouse when
subsecond KQL exploration over incoming events is required. Do not force one
store merely to avoid architecture decisions. Troubleshoot a poor fit by
measuring ingestion delay, scan volume, concurrency waits, update complexity,
and duplicated copies. Mini-lab: rank all four stores for (1) images plus JSON,
(2) a finance star schema, (3) live device logs, and (4) order entry, explaining
which requirement eliminated each alternative.

## Dataflow Gen2 transformation clinic

<!-- block-id: transform-tool-model -->
Tool choice combines authoring model and execution locality. Dataflow Gen2 uses
the Power Query engine and a visual sequence of M transformations. A notebook
uses code and Spark for distributed, library-driven processing. T-SQL executes
set-based relational logic near warehouse data. KQL executes pipeline-shaped
event and time-series logic near Eventhouse data. Moving data to a favorite
language can cost more than using the engine already holding it.

<!-- block-id: transform-tool-operations -->
A disciplined Dataflow Gen2 build follows this order: connect with a governed
connection; profile source columns; set locale-aware types; remove unused
columns and filter rows early; normalize text and null representations; define
keys; merge or append; reshape; calculate derived values; validate row counts
and errors; select a supported destination and update method; publish and
monitor refresh. Name queries and steps for business meaning. Separate staging
queries from destination queries and disable load for helpers when appropriate.

<!-- block-id: dataflow-types-and-cleaning -->
Types are semantic, not cosmetic. Text `"01/02/2026"` can mean different dates
by locale; decimal currency and floating point have different guarantees;
joining numeric `42` to text `"42"` can fail or coerce unexpectedly. Assign type
with an explicit locale, inspect conversion errors, and decide whether invalid
values are corrected, replaced, or quarantined. Use trim/clean and case rules
before key comparison. Replace null only when zero or a default has defensible
business meaning; “unknown” and “none” are not generally interchangeable.

<!-- block-id: dataflow-combining -->
**Merge** joins columns using key equality and a join kind: left outer preserves
all left rows; inner keeps matches; anti joins isolate missing/unexpected keys.
**Append** stacks rows and aligns columns by name, producing null for absent
fields. Before merging, prove uniqueness on the expected one-side. Afterward,
compare row counts and unmatched keys. Before appending monthly extracts,
standardize names and types and add source-period metadata. A fuzzy merge may
help entity matching but requires thresholds and human-reviewed error cases; it
is not a substitute for a governed key.

<!-- block-id: dataflow-reshaping -->
Group By changes grain and should output only grouping keys plus aggregates.
Pivot turns values into columns and needs an aggregation when a cell has
multiple rows. Unpivot turns repeated columns such as `Jan`, `Feb`, `Mar` into
attribute/value rows and is often safer for evolving periods. Split, extract,
and conditional columns should preserve the original value until validation is
complete. Compute ratios from aggregated numerator and denominator rather than
averaging row-level percentages unless the measure definition explicitly calls
for it.

<!-- block-id: dataflow-folding -->
Query folding lets the connector translate supported Power Query steps into a
source query. Place selective filters, projections, and supported joins early;
inspect folding indicators or native query where available. A custom function,
unsupported type conversion, privacy boundary, or nonfoldable source can stop
folding at that step and everything after it. The consequence is often a large
source read and mashup-engine processing—not refresh failure. Use staged/native
queries cautiously, preserve parameterization, and compare source rows scanned
plus refresh duration before and after a change.

<!-- block-id: transform-tool-decisions -->
Choose Dataflow Gen2 when maintainers value visual Power Query, transformations
are tabular, and managed destinations fit. Choose notebooks for complex
algorithms, custom packages, reusable tests, distributed tuning, or mixed
file/table work. Choose T-SQL for relational transformations within a warehouse,
especially joins, window functions, and dimensional loads. Choose KQL for logs,
dynamic payloads, time bins, sequence, and high-rate event analysis. Limitations
include Dataflow folding/connector variability, notebook startup and engineering
overhead, T-SQL's relational boundary, and KQL's different update/serving model.

<!-- block-id: transform-tool-example -->
**Worked Dataflow.** Import `Orders` and `Customers`; explicitly type
`OrderDate`, `CustomerId`, and `Amount`; filter to the requested period; left
anti-join Orders to Customers to create an unmatched-key quality query; left
join valid orders to Customers; unpivot monthly target columns; group by Region
and Month; calculate Revenue and OrderCount; load the curated output and quality
output separately. Verify folding through the source filter and projection,
then compare input rows, valid rows, unmatched rows, and output totals.

<!-- block-id: transform-tool-diagnostics -->
For Dataflow failures, open refresh details and find the first failing query and
step. Separate connection/gateway errors, source schema drift, type conversion,
privacy/firewall constraints, folding/performance, and destination write errors.
Reproduce with a filtered representative sample but retest at scale. For wrong
results, check join cardinality, nulls, locale/types, grouping grain, and
implicit conversions. Mini-lab: build the worked flow, deliberately duplicate a
Customer key and add an invalid date; prove the quality outputs expose both
without silently changing sales totals.

## Shortcuts and mirroring

<!-- block-id: shortcuts-comprehensive -->
A OneLake shortcut is metadata that exposes a target path under another OneLake
location. Internal shortcuts reference Fabric/OneLake data; external shortcuts
use a connection to supported storage. Create the connection with least
privilege, choose a unique shortcut name and correct target, and place supported
Delta tables under `Tables` or general content under `Files`. Validate Spark,
SQL, or other intended access and define who owns credential rotation, source
schema changes, cache behavior, and target availability. Deleting the shortcut
deletes the reference, not target data; deleting or moving the target breaks the
reference. Choose a shortcut to avoid copying selected existing data, not when
you need isolation from source outages or a transformed historical snapshot.

**Failure lab.** Create a test shortcut, query a known row count, revoke source
read, and observe the error without changing the target. Restore permission,
then rename or move a test target and diagnose the reference. Check shortcut
path, connection identity, source ACL, supported format, Delta log, schema
refresh/synchronization, and any cache or acceleration layer. A user may have
access to the shortcut item but lack source data authorization through the
chosen credential path.

<!-- block-id: mirroring-comprehensive -->
Mirroring represents a broader, continuously synchronized source. Database
mirroring captures supported operational changes into read-only analytical
Delta representation. Metadata mirroring synchronizes catalog metadata and
uses shortcuts to open data in place. Open mirroring accepts correctly formed
change data written to a Fabric landing zone. Verify source/version support,
network and authentication, required source privileges, key/change semantics,
capacity, and unsupported data types before creation. Select source objects,
start replication, monitor initial snapshot and ongoing lag, and validate counts
and changes—including deletes.

Choose mirroring for low-friction replication or catalog-wide access when the
source fits; choose shortcut for selected in-place open data; choose pipeline
copy for scheduled/custom mappings and transformations. Do not write directly
to a mirrored target as if it were the operational source. For stale data,
inspect source change capture/retention, replication status, rejected tables or
types, permissions, capacity, and lag. Mini-lab: insert, update, and delete one
source row, record when each appears, pause or break connectivity, and prove the
monitoring evidence identifies the last synchronized point.

## Pipeline ingestion

<!-- block-id: pipelines-comprehensive -->
Copy Activity separates source connection, source query/path, column mapping,
sink behavior, and performance settings. Build a parameterized pipeline with
typed source/destination identifiers, validate them against an allow-list, and
use dynamic expressions only to assemble controlled values. Configure explicit
mapping when schema stability matters. Capture a run ID and source version,
write rejects separately, and validate rows read, copied, skipped, and written.
Grant the pipeline identity only the necessary read and target write rights;
store secrets in managed connections, not parameters or logs.

Tune from measurements: source query selectivity, partitioned reads, parallel
copies, ForEach concurrency, staging, sink batch/commit behavior, network, and
capacity. More parallelism can throttle a source or create small files. Retry
transient network or throttling faults with backoff; repair authentication,
mapping, constraint, and type errors before rerun. Mini-lab: copy two date
partitions through one parameterized child pipeline, force one deterministic
mapping error, verify only that partition fails, correct it, and rerun without
duplicating the successful partition.

## Language translation clinic

<!-- block-id: languages-comprehensive -->
PySpark, T-SQL, and KQL share relational ideas but differ in type systems,
null semantics, physical execution, and durable write behavior. A sound
procedure is filter/select early, make types explicit, validate keys, transform,
write to the engine-native target, and reconcile counts/totals. PySpark can
distribute file/Delta work and expose Spark plans; T-SQL uses relational plans,
constraints, and transactions in a warehouse; KQL excels at time-bounded event
pipelines and dynamic values. Avoid collecting large Spark data to the driver,
unbounded KQL scans, or row-by-row SQL operations.

**Equivalent join and aggregate:** the PySpark shape is:

```python
orders.join(customers, "CustomerId", "left").groupBy("Region").agg(sum("Amount"))
```

In T-SQL use a `LEFT JOIN` plus `GROUP BY`; in KQL use `join kind=leftouter`
then `summarize`.
Before declaring equivalence, decide how unmatched keys, duplicate customer
rows, null regions, decimal precision, and event-time bounds behave. Mini-lab:
run a six-row fixture containing each edge case in all three engines and compare
the ordered normalized result, not just that each query completed.

## Denormalization, aggregation, and quality

<!-- block-id: denormalize-comprehensive -->
Denormalization creates a consumer-oriented shape by joining descriptive data
at a declared output grain. Confirm every joined lookup has at most one winning
row for each fact at the relevant time. Select only needed attributes and decide
whether history is current-state or as-of-event. Compare fact row count, distinct
fact key, unmatched count, and additive totals before and after. A flattened
table simplifies consumption and can improve scans, but repeats attributes,
increases storage/update cost, and can become inconsistent if refresh timing is
not governed. Mini-lab: introduce two current dimension rows for one key and
show how a $10 fact becomes $20 after the join; repair the winning-row rule.

<!-- block-id: aggregate-comprehensive -->
Aggregation replaces detail grain with grouping grain. Define keys and measure
algebra first: additive measures sum across all intended dimensions;
semi-additive measures such as balance may sum across accounts but not time;
nonadditive ratios and distinct counts need special handling. Track numerator
and denominator for recomputable ratios, define null behavior, and avoid
double-counting after joins. Incremental aggregate maintenance must restate a
bucket when a late change affects it. Mini-lab: calculate daily revenue, closing
inventory, average price, and distinct customers; explain why four identical
`SUM` operations would be wrong.

<!-- block-id: data-quality-comprehensive -->
Data quality is an explicit disposition system. Define rules for key uniqueness,
required values, valid domains/ranges, referential integrity, and timeliness.
For duplicates, keep a winner only from a trusted ordering and retain evidence
of losers. For missing data, distinguish unknown, not applicable, delayed, and
invalid before defaulting. For late data, use overlap/replay, reopen affected
partitions, resolve late dimensions, and restate downstream aggregates. Each
run records rule ID, evaluated count, failed count/rate, sample/reference,
source version, disposition, and owner.

Quarantine preserves bad records for correction without contaminating curated
outputs; it is not a permanent trash folder. Define replay and expiry. If a rule
fails suddenly, check source schema/version and code deployment before blaming
the data. Mini-lab: process a fixture with one exact duplicate, one newer update,
one null amount, one unknown customer, and one yesterday event arriving today;
predict the winner, quarantine, unknown-member handling, and which daily
aggregate must be restated.

<!-- block-id: batch-exam-distinctions -->
Shortcuts reference selected data in place; mirroring continuously represents a
supported database or catalog; Copy Activity moves a bounded selection. Merge
joins columns; append stacks rows. Query folding is source execution, not merely
successful refresh. Denormalization changes shape and may preserve grain;
aggregation intentionally changes grain. A null-replacement step is not a data
quality strategy unless the business meaning and audit trail are defined.

<!-- block-id: batch-recall-lab -->
**Recall.** Which store fits concurrent star-schema T-SQL? What evidence proves
a Dataflow filter folded? Why can a left join increase row count? How does a
shortcut's credential path differ from copied data? Which mirroring mode uses a
published change-file contract? Why should aggregate ratios retain components?
For practice, take one customer/order dataset through Dataflow, PySpark, SQL,
and KQL; document types, joins, quality dispositions, output grain, and expected
totals before comparing results.

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
