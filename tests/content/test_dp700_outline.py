"""Official DP-700 blueprint representation tests."""

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
