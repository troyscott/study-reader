# Book content model

Study Reader separates authored chapters from application code. A published
book is a directory containing `book.yaml` and a `chapters/` directory of
Markdown files.

## Stable identifiers

- Book, domain, chapter, source, and objective identifiers MUST be lowercase,
  human-readable, and stable after publication.
- Chapter slugs MUST be unique within a book and MUST remain stable when a title
  changes.
- Objective identifiers SHOULD describe their hierarchy, such as
  `ingest.streaming.windows`.
- An explicit `<!-- block-id: durable-name -->` marker assigns a durable anchor
  to the next top-level Markdown block. Authors SHOULD use explicit block IDs
  for important passages that may receive bookmarks, highlights, or notes.
- Blocks without explicit markers receive deterministic section-and-position
  identifiers. Those fallbacks survive ordinary wording edits but MAY change if
  blocks are inserted or reordered in the same section.

## Ordering

YAML list order is authoritative. Domain order follows the official skills
outline. Chapter order follows the subdomains within each domain. Objective
order follows the bullet order in the effective official blueprint. The reader
MUST NOT infer order from identifiers or filenames.

## Sources and ownership

Every chapter MUST map to at least one source declared in its book manifest.
The manifest records the official blueprint URL and effective date. Each source
record contains its canonical Microsoft Learn URL, retrieval timestamp, SHA-256
content hash, and direct chapter mappings. Source-to-chapter and
chapter-to-source mappings MUST agree so that a future refresh can identify the
affected chapters without a lineage service.

Only `https://learn.microsoft.com` sources are accepted by the published
content contract. Raw retrieval responses are working data and MUST NOT be
committed as public content. The later refresh milestone will add bounded
retrieval, normalization, conditional requests, and readable change summaries;
the registry deliberately does not attempt to generalize those mappings into a
dependency graph.

Microsoft Learn remains authoritative for Microsoft exam objectives and product
behavior. Markdown chapters MUST contain original study-oriented writing and
MUST NOT reproduce Microsoft Learn pages wholesale.

## Authoring depth

The official study guide is the coverage contract, not the finished teaching
material. Every measured objective in a published chapter MUST receive
substantive coverage. A title match or repeated bullet is insufficient.

For each objective, authors SHOULD provide the elements that materially aid
understanding:

- an orientation and conceptual model;
- precise terminology and responsibility boundaries;
- decision criteria, trade-offs, and common failure modes;
- a worked configuration, query, transformation, or scenario when applicable;
- exam distinctions that separate easily confused features;
- active-recall questions; and
- exact authoritative links.

Microsoft Learn is authoritative for Microsoft Fabric behavior. Chapters MAY
link to primary specifications or official upstream projects for underlying
concepts such as SQL, Apache Spark, Apache Airflow, Delta Lake, or Apache Kafka.
Those links supplement rather than override Microsoft Learn for Fabric-specific
claims.

For example, coverage of Dataflow Gen2 MUST explain the transformations a
learner is expected to reason about—such as data types, filtering, joins,
grouping, shaping, schema handling, and query folding—along with destinations
and tool-selection trade-offs. Merely listing “Dataflow Gen2” does not satisfy
the objective.

### Comprehensive coverage audit

Each published book MUST include a `coverage.yaml` file with exactly one record
for every measured objective in `book.yaml`. The record identifies the owning
chapter, the objective's required subtopics, its authoritative sources, known
gaps, and durable Markdown block IDs that provide evidence for the approved
teaching rubric.

An objective MAY move through `planned`, `draft`, and `complete` states. A
non-complete objective MUST state its remaining gaps. An objective MUST NOT be
marked `complete` unless it has no remaining gaps and identifies durable blocks
for all of these evidence categories:

- conceptual model and terminology;
- prerequisites, responsibilities, and security boundaries;
- procedure or operational workflow;
- decision guidance and trade-offs;
- a worked example;
- limitations and failure modes;
- troubleshooting or monitoring guidance;
- exam distinctions;
- at least two active-recall questions; and
- a scenario or mini-lab.

One strong block MAY support more than one category or objective when its
content genuinely supplies that evidence. The evidence mapping exists to make
editorial review inspectable; it MUST NOT be satisfied with empty headings,
duplicated boilerplate, or identifiers that are absent from the chapter.

## Validation

Pydantic rejects duplicate identifiers, duplicate slugs, non-Learn source
hosts, malformed hashes, one-way source mappings, broken source references,
invalid paths, and unknown manifest fields. Content tests confirm that every
planned chapter file exists and maps at least one objective and one source. The
coverage audit additionally rejects missing or extra objectives, incorrect
chapter ownership, invalid source mappings, unsupported completion claims, and
incomplete objectives that conceal their remaining gaps.
Rendering tests verify sanitized HTML, stable anchors, external-link behavior,
and a reviewed golden fixture.
