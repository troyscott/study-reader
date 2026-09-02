"""Reusable book-contract tests."""

from datetime import date

import pytest
from pydantic import HttpUrl, ValidationError

from study_reader.content.models import Book, Chapter, Domain, Objective, Source


def minimal_book() -> Book:
    """Build a non-DP-700 book to prove the schema is exam-agnostic."""

    return Book(
        id="exam-xyz",
        exam_code="XY-100",
        title="Example certification reader",
        blueprint_effective_date=date(2026, 1, 1),
        blueprint_url=HttpUrl("https://learn.microsoft.com/example"),
        sources=[
            Source(
                id="official-guide",
                title="Official guide",
                url=HttpUrl("https://learn.microsoft.com/example"),
            )
        ],
        domains=[
            Domain(
                id="design",
                title="Design a solution",
                weight="100%",
                chapters=[
                    Chapter(
                        id="design-basics",
                        slug="design-basics",
                        title="Design basics",
                        content_path="design-basics.md",
                        objectives=[
                            Objective(id="design.choose", title="Choose a design")
                        ],
                        source_ids=["official-guide"],
                    )
                ],
            )
        ],
    )


def test_book_contract_is_not_hard_coded_to_dp700() -> None:
    book = minimal_book()

    assert book.exam_code == "XY-100"
    assert book.chapter_count == 1
    assert book.chapter_by_slug("design-basics").id == "design-basics"


def test_book_rejects_duplicate_stable_identifiers() -> None:
    book_data = minimal_book().model_dump()
    book_data["domains"] = (*book_data["domains"], book_data["domains"][0])

    with pytest.raises(ValidationError, match="domain identifiers must be unique"):
        Book.model_validate(book_data)


def test_book_rejects_unknown_source_mapping() -> None:
    book_data = minimal_book().model_dump()
    book_data["domains"][0]["chapters"][0]["source_ids"] = ["missing"]

    with pytest.raises(ValidationError, match="unknown source"):
        Book.model_validate(book_data)
