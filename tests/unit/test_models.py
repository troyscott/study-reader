"""Reusable book-contract tests."""

from datetime import UTC, date, datetime

import pytest
from pydantic import HttpUrl, ValidationError

from study_reader.content.coverage import (
    CoverageAudit,
    CoverageEvidence,
    ObjectiveCoverage,
)
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
                retrieved_at=datetime(2026, 1, 2, tzinfo=UTC),
                content_sha256="a" * 64,
                chapter_ids=["design-basics"],
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


def test_book_rejects_non_learn_sources() -> None:
    book_data = minimal_book().model_dump()
    book_data["sources"][0]["url"] = "https://example.com/guide"

    with pytest.raises(ValidationError, match="not hosted on Microsoft Learn"):
        Book.model_validate(book_data)


def test_book_rejects_one_way_source_mapping() -> None:
    book_data = minimal_book().model_dump()
    secondary_source = {
        **book_data["sources"][0],
        "id": "secondary-guide",
        "title": "Secondary official guide",
    }
    book_data["sources"] = (*book_data["sources"], secondary_source)

    with pytest.raises(ValidationError, match="mappings must be bidirectional"):
        Book.model_validate(book_data)


def test_coverage_audit_matches_an_exam_agnostic_book() -> None:
    book = minimal_book()
    audit = CoverageAudit(
        book_id=book.id,
        blueprint_effective_date=book.blueprint_effective_date,
        objectives=[
            ObjectiveCoverage(
                objective_id="design.choose",
                chapter_id="design-basics",
                status="draft",
                subtopics=["Constraints", "Trade-offs"],
                source_ids=["official-guide"],
                gaps=["Add a worked example"],
            )
        ],
    )

    audit.validate_against(book)


def test_complete_coverage_requires_every_evidence_category() -> None:
    with pytest.raises(ValidationError, match="every evidence category"):
        ObjectiveCoverage(
            objective_id="design.choose",
            chapter_id="design-basics",
            status="complete",
            subtopics=["Constraints", "Trade-offs"],
            source_ids=["official-guide"],
        )


def test_complete_coverage_rejects_remaining_gaps() -> None:
    evidence = CoverageEvidence(
        **{name: name.replace("_", "-") for name in CoverageEvidence.model_fields}
    )

    with pytest.raises(ValidationError, match="cannot retain coverage gaps"):
        ObjectiveCoverage(
            objective_id="design.choose",
            chapter_id="design-basics",
            status="complete",
            subtopics=["Constraints", "Trade-offs"],
            source_ids=["official-guide"],
            gaps=["Still incomplete"],
            evidence=evidence,
        )


def test_complete_coverage_requires_evidence_blocks_in_its_chapter() -> None:
    book = minimal_book()
    evidence = CoverageEvidence(
        **{name: "design-evidence" for name in CoverageEvidence.model_fields}
    )
    audit = CoverageAudit(
        book_id=book.id,
        blueprint_effective_date=book.blueprint_effective_date,
        objectives=[
            ObjectiveCoverage(
                objective_id="design.choose",
                chapter_id="design-basics",
                status="complete",
                subtopics=["Constraints", "Trade-offs"],
                source_ids=["official-guide"],
                evidence=evidence,
            )
        ],
    )

    with pytest.raises(ValueError, match="missing evidence blocks"):
        audit.validate_evidence_blocks({"design-basics": "# Design basics"})

    audit.validate_evidence_blocks(
        {"design-basics": "<!-- block-id: design-evidence -->\nEvidence."}
    )
