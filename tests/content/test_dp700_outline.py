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


def test_source_registry_records_current_learn_provenance() -> None:
    book = BookCatalog(CONTENT_ROOT).load_book("dp700")

    assert len(book.sources) == 9
    assert {source.url.host for source in book.sources} == {"learn.microsoft.com"}
    assert all(source.retrieved_at.tzinfo is not None for source in book.sources)
    assert all(len(source.content_sha256) == 64 for source in book.sources)
    assert set(book.sources[0].chapter_ids) == {chapter.id for chapter in book.chapters}


def test_representative_chapter_is_published_and_directly_sourced() -> None:
    catalog = BookCatalog(CONTENT_ROOT)
    book = catalog.load_book("dp700")
    chapter = book.chapter_by_slug("workspace-settings")
    markdown = catalog.load_chapter_markdown(book, chapter)

    assert chapter.status == "published"
    assert len(chapter.source_ids) == 9
    assert all(objective.title in markdown for objective in chapter.objectives)
    assert "## Configure Spark workspace settings" in markdown
    assert "## Configure domain workspace settings" in markdown
    assert "## What the OneLake settings control" in markdown
    assert "## Configure Apache Airflow workspace settings" in markdown
    assert "## Responsibility and prerequisite boundaries" in markdown
    assert "## Exam distinctions" in markdown
    assert "## Active recall" in markdown
    assert "OneLake.Read.All" in markdown
