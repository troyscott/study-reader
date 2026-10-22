"""Read validated published books from the Git-backed content directory."""

import re
from pathlib import Path

import yaml

from study_reader.content.coverage import CoverageAudit
from study_reader.content.models import Book, Chapter

SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class BookCatalog:
    """A read-only catalog over published book manifests and Markdown."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def load_book(self, book_id: str) -> Book:
        """Load and validate one book manifest without permitting path traversal."""

        if not SAFE_ID.fullmatch(book_id):
            raise FileNotFoundError(book_id)
        manifest_path = self.root / book_id / "book.yaml"
        try:
            raw_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise FileNotFoundError(book_id) from error
        return Book.model_validate(raw_manifest)

    def chapter_path(self, book: Book, chapter: Chapter) -> Path:
        """Return the chapter path constrained to its validated book directory."""

        return self.root / book.id / "chapters" / chapter.content_path

    def load_coverage_audit(self, book: Book) -> CoverageAudit:
        """Load and validate the objective-level content evidence contract."""

        audit_path = self.root / book.id / "coverage.yaml"
        try:
            raw_audit = yaml.safe_load(audit_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise FileNotFoundError(audit_path) from error
        audit = CoverageAudit.model_validate(raw_audit)
        audit.validate_against(book)
        audit.validate_evidence_blocks(
            {
                chapter.id: self.load_chapter_markdown(book, chapter)
                for chapter in book.chapters
            }
        )
        return audit

    def load_chapter_markdown(self, book: Book, chapter: Chapter) -> str:
        """Read one authored chapter from the published snapshot."""

        return self.chapter_path(book, chapter).read_text(encoding="utf-8")
