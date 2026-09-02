"""Exam-agnostic, validated book content models."""

from datetime import date, datetime
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ContentModel(BaseModel):
    """Strict immutable base for published content contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Source(ContentModel):
    """An authoritative source cited by one or more chapters."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    url: HttpUrl
    retrieved_at: datetime
    content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    chapter_ids: tuple[str, ...] = Field(min_length=1)


class Objective(ContentModel):
    """One measured skill mapped to a study chapter."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]*$")
    title: str = Field(min_length=1)


class Chapter(ContentModel):
    """One reflowable chapter and its exam objective mappings."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    content_path: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*\.md$")
    objectives: tuple[Objective, ...] = Field(min_length=1)
    source_ids: tuple[str, ...] = Field(min_length=1)
    status: str = Field(
        default="placeholder", pattern=r"^(placeholder|draft|published)$"
    )


class Domain(ContentModel):
    """An ordered exam skill domain containing ordered chapters."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    title: str = Field(min_length=1)
    weight: str = Field(pattern=r"^(?:\d{1,3}[\u2013-]\d{1,3}|\d{1,3})%$")
    chapters: tuple[Chapter, ...] = Field(min_length=1)


class Book(ContentModel):
    """A versioned certification book derived from an official blueprint."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    exam_code: str = Field(pattern=r"^[A-Z]{2,5}-\d{3}$")
    title: str = Field(min_length=1)
    blueprint_effective_date: date
    blueprint_url: HttpUrl
    sources: tuple[Source, ...] = Field(min_length=1)
    domains: tuple[Domain, ...] = Field(min_length=1)

    @cached_property
    def chapters(self) -> tuple[Chapter, ...]:
        """Flatten chapters while preserving manifest order."""

        return tuple(chapter for domain in self.domains for chapter in domain.chapters)

    @property
    def chapter_count(self) -> int:
        """Return the total number of ordered chapters."""

        return len(self.chapters)

    def chapter_by_slug(self, slug: str) -> Chapter:
        """Find a chapter by stable slug."""

        for chapter in self.chapters:
            if chapter.slug == slug:
                return chapter
        raise KeyError(slug)

    def chapter_position(self, chapter: Chapter) -> int:
        """Return the chapter's zero-based position."""

        return self.chapters.index(chapter)

    @model_validator(mode="after")
    def validate_references_and_identifiers(self) -> Self:
        """Reject ambiguous identifiers and broken source mappings."""

        domain_ids = [domain.id for domain in self.domains]
        if len(domain_ids) != len(set(domain_ids)):
            raise ValueError("domain identifiers must be unique")

        chapter_ids = [chapter.id for chapter in self.chapters]
        chapter_slugs = [chapter.slug for chapter in self.chapters]
        if len(chapter_ids) != len(set(chapter_ids)):
            raise ValueError("chapter identifiers must be unique")
        if len(chapter_slugs) != len(set(chapter_slugs)):
            raise ValueError("chapter slugs must be unique")

        objective_ids = [
            objective.id
            for chapter in self.chapters
            for objective in chapter.objectives
        ]
        if len(objective_ids) != len(set(objective_ids)):
            raise ValueError("objective identifiers must be unique")

        source_ids = [source.id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source identifiers must be unique")

        chapter_id_set = set(chapter_ids)
        for source in self.sources:
            if source.url.host != "learn.microsoft.com":
                raise ValueError(f"source {source.id} is not hosted on Microsoft Learn")
            unknown_chapters = set(source.chapter_ids) - chapter_id_set
            if unknown_chapters:
                raise ValueError(
                    f"source {source.id} maps unknown chapters: "
                    f"{sorted(unknown_chapters)}"
                )

        source_id_set = set(source_ids)
        for chapter in self.chapters:
            unknown_sources = set(chapter.source_ids) - source_id_set
            if unknown_sources:
                raise ValueError(
                    f"chapter {chapter.id} references unknown source: "
                    f"{sorted(unknown_sources)}"
                )

        for source in self.sources:
            referencing_chapters = {
                chapter.id
                for chapter in self.chapters
                if source.id in chapter.source_ids
            }
            if referencing_chapters != set(source.chapter_ids):
                raise ValueError(
                    f"source {source.id} chapter mappings must be bidirectional"
                )
        return self
