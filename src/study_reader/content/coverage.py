"""Objective-level evidence contract for comprehensive study content."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from study_reader.content.markdown import BLOCK_MARKER
from study_reader.content.models import Book

BLOCK_ID = r"^[a-z0-9][a-z0-9-]*$"
OBJECTIVE_ID = r"^[a-z0-9][a-z0-9.-]*$"


class CoverageModel(BaseModel):
    """Strict immutable base for coverage records."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class CoverageEvidence(CoverageModel):
    """Durable Markdown blocks that prove an objective's teaching depth."""

    conceptual_model: str | None = Field(default=None, pattern=BLOCK_ID)
    prerequisites: str | None = Field(default=None, pattern=BLOCK_ID)
    procedure: str | None = Field(default=None, pattern=BLOCK_ID)
    decision_guidance: str | None = Field(default=None, pattern=BLOCK_ID)
    worked_example: str | None = Field(default=None, pattern=BLOCK_ID)
    limitations: str | None = Field(default=None, pattern=BLOCK_ID)
    troubleshooting: str | None = Field(default=None, pattern=BLOCK_ID)
    exam_distinctions: str | None = Field(default=None, pattern=BLOCK_ID)
    recall_questions: str | None = Field(default=None, pattern=BLOCK_ID)
    scenario_lab: str | None = Field(default=None, pattern=BLOCK_ID)

    @property
    def block_ids(self) -> tuple[str, ...]:
        """Return all recorded evidence block identifiers."""

        return tuple(
            value
            for name in type(self).model_fields
            if (value := getattr(self, name)) is not None
        )

    @property
    def is_complete(self) -> bool:
        """Return whether every rubric category has durable evidence."""

        return len(self.block_ids) == len(type(self).model_fields)


class ObjectiveCoverage(CoverageModel):
    """Coverage plan and evidence for one measured objective."""

    objective_id: str = Field(pattern=OBJECTIVE_ID)
    chapter_id: str = Field(pattern=BLOCK_ID)
    status: Literal["planned", "draft", "complete"]
    subtopics: tuple[str, ...] = Field(min_length=2)
    source_ids: tuple[str, ...] = Field(min_length=1)
    gaps: tuple[str, ...] = ()
    evidence: CoverageEvidence = Field(default_factory=CoverageEvidence)

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        """Make completion a claim backed by every rubric category."""

        if self.status == "complete" and not self.evidence.is_complete:
            raise ValueError("complete objectives require every evidence category")
        if self.status == "complete" and self.gaps:
            raise ValueError("complete objectives cannot retain coverage gaps")
        if self.status != "complete" and not self.gaps:
            raise ValueError("incomplete objectives must record coverage gaps")
        return self


class CoverageAudit(CoverageModel):
    """Book-wide, objective-level comprehensive-content contract."""

    book_id: str = Field(pattern=BLOCK_ID)
    blueprint_effective_date: date
    objectives: tuple[ObjectiveCoverage, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_objectives(self) -> Self:
        """Reject ambiguous coverage claims."""

        objective_ids = [objective.objective_id for objective in self.objectives]
        if len(objective_ids) != len(set(objective_ids)):
            raise ValueError("coverage objective identifiers must be unique")
        return self

    def validate_against(self, book: Book) -> None:
        """Verify exact objective, chapter, source, and blueprint mappings."""

        if self.book_id != book.id:
            raise ValueError("coverage book identifier does not match manifest")
        if self.blueprint_effective_date != book.blueprint_effective_date:
            raise ValueError("coverage blueprint date does not match manifest")

        expected = {
            objective.id: chapter
            for chapter in book.chapters
            for objective in chapter.objectives
        }
        actual = {coverage.objective_id: coverage for coverage in self.objectives}
        if actual.keys() != expected.keys():
            raise ValueError("coverage objectives must exactly match the book manifest")

        known_sources = {source.id for source in book.sources}
        for objective_id, coverage in actual.items():
            chapter = expected[objective_id]
            if coverage.chapter_id != chapter.id:
                raise ValueError(f"coverage chapter mismatch for {objective_id}")
            if not set(coverage.source_ids) <= known_sources:
                raise ValueError(f"unknown coverage source for {objective_id}")
            if not set(coverage.source_ids) <= set(chapter.source_ids):
                raise ValueError(f"coverage source not mapped to {chapter.id}")

    def validate_evidence_blocks(self, chapter_markdown: dict[str, str]) -> None:
        """Verify that completion evidence names durable blocks in its chapter."""

        for coverage in self.objectives:
            if coverage.status != "complete":
                continue
            markdown = chapter_markdown.get(coverage.chapter_id)
            if markdown is None:
                raise ValueError(f"missing chapter content for {coverage.chapter_id}")
            block_ids = {
                marker.group(1)
                for line in markdown.splitlines()
                if (marker := BLOCK_MARKER.fullmatch(line)) is not None
            }
            missing = set(coverage.evidence.block_ids) - block_ids
            if missing:
                missing_list = ", ".join(sorted(missing))
                raise ValueError(
                    f"missing evidence blocks for {coverage.objective_id}: "
                    f"{missing_list}"
                )
