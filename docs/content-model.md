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
The manifest records the official blueprint URL and effective date. Additional
chapter-specific sources will record retrieval dates and hashes in the refresh
milestone.

Microsoft Learn remains authoritative for Microsoft exam objectives and product
behavior. Markdown chapters MUST contain original study-oriented writing and
MUST NOT reproduce Microsoft Learn pages wholesale.

## Validation

Pydantic rejects duplicate identifiers, duplicate slugs, broken source
references, invalid paths, and unknown manifest fields. Content tests confirm
that every planned chapter file exists and maps at least one objective and one
source. Rendering tests verify sanitized HTML, stable anchors, external-link
behavior, and a reviewed golden fixture.
