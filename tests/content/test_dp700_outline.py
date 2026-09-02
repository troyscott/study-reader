"""Official DP-700 blueprint and source-registry tests."""

from datetime import date
from pathlib import Path

from study_reader.content.catalog import BookCatalog

CONTENT_ROOT = Path("content/published")


def test_dp700_outline_matches_current_official_structure() -> None:
    book = BookCatalog(CONTENT_ROOT).load_book("dp700")

    assert book.exam_code == "DP-700"
    assert book.blueprint_effective_date == date(2026, 7, 21)
    assert str(book.blueprint_url) == (
        "https://learn.microsoft.com/en-us/credentials/certifications/"
        "resources/study-guides/dp-700"
    )
    assert [(domain.title, domain.weight) for domain in book.domains] == [
        ("Implement and manage an analytics solution", "30\u201335%"),
        ("Ingest and transform data", "30\u201335%"),
        ("Monitor and optimize an analytics solution", "30\u201335%"),
    ]
    assert [len(domain.chapters) for domain in book.domains] == [4, 3, 3]
    assert book.chapter_count == 10


def test_every_dp700_chapter_maps_objectives_sources_and_content() -> None:
    catalog = BookCatalog(CONTENT_ROOT)
    book = catalog.load_book("dp700")

    for chapter in book.chapters:
        assert chapter.objectives
        assert chapter.source_ids
        assert catalog.chapter_path(book, chapter).is_file()

    assert sum(len(chapter.objectives) for chapter in book.chapters) == 54


def test_dp700_coverage_audit_records_every_objective_and_known_gap() -> None:
    catalog = BookCatalog(CONTENT_ROOT)
    book = catalog.load_book("dp700")
    audit = catalog.load_coverage_audit(book)

    assert len(audit.objectives) == 54
    assert {coverage.objective_id for coverage in audit.objectives} == {
        objective.id for chapter in book.chapters for objective in chapter.objectives
    }
    assert all(len(coverage.subtopics) >= 2 for coverage in audit.objectives)
    assert all(coverage.source_ids for coverage in audit.objectives)
    assert all(coverage.gaps for coverage in audit.objectives)
    assert all(coverage.status == "draft" for coverage in audit.objectives)


def test_source_registry_records_current_learn_provenance() -> None:
    book = BookCatalog(CONTENT_ROOT).load_book("dp700")

    assert len(book.sources) >= 30
    assert {source.url.host for source in book.sources} == {"learn.microsoft.com"}
    assert all(source.retrieved_at.tzinfo is not None for source in book.sources)
    assert all(len(source.content_sha256) == 64 for source in book.sources)
    assert set(book.sources[0].chapter_ids) == {chapter.id for chapter in book.chapters}


def test_every_chapter_is_published_substantive_and_directly_sourced() -> None:
    catalog = BookCatalog(CONTENT_ROOT)
    book = catalog.load_book("dp700")

    for chapter in book.chapters:
        markdown = catalog.load_chapter_markdown(book, chapter)

        assert chapter.status == "published"
        assert len(chapter.source_ids) >= 2
        assert len(markdown.split()) >= 700
        assert all(objective.title in markdown for objective in chapter.objectives)
        assert "## Objective coverage" in markdown
        assert "## Exam distinctions" in markdown
        assert "## Active recall" in markdown
        assert (
            "## Authoritative sources" in markdown
            or "## Sources and provenance" in markdown
        )
        assert "Planned study work" not in markdown
        assert "placeholder" not in markdown.lower()


def test_workspace_settings_retains_representative_technical_depth() -> None:
    catalog = BookCatalog(CONTENT_ROOT)
    book = catalog.load_book("dp700")
    chapter = book.chapter_by_slug("workspace-settings")
    markdown = catalog.load_chapter_markdown(book, chapter)

    assert len(chapter.source_ids) == 9
    assert "## Configure Spark workspace settings" in markdown
    assert "## Configure domain workspace settings" in markdown
    assert "## What the OneLake settings control" in markdown
    assert "## Configure Apache Airflow workspace settings" in markdown
    assert "## Responsibility and prerequisite boundaries" in markdown
    assert "OneLake.Read.All" in markdown
