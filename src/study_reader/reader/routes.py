"""Routes exposed by the public reader."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from starlette.responses import Response

from study_reader.content.catalog import BookCatalog
from study_reader.content.markdown import render_markdown
from study_reader.content.models import Book, Chapter, Domain

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def domain_for_chapter(book: Book, chapter: Chapter) -> Domain:
    """Return the domain containing a chapter."""

    for domain in book.domains:
        if chapter in domain.chapters:
            return domain
    raise KeyError(chapter.id)


@router.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    """Open the representative chapter in the first published book."""

    return RedirectResponse(
        url="/books/dp700/chapters/workspace-settings",
        status_code=307,
    )


@router.get("/books/{book_id}", include_in_schema=False)
async def book_home(request: Request, book_id: str) -> RedirectResponse:
    """Open the first chapter in a validated book."""

    catalog = BookCatalog(request.app.state.settings.published_content_dir)
    try:
        book = catalog.load_book(book_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Book not found") from error
    return RedirectResponse(
        url=f"/books/{book.id}/chapters/{book.chapters[0].slug}",
        status_code=307,
    )


@router.get("/books/{book_id}/chapters/{chapter_slug}", include_in_schema=False)
async def chapter(request: Request, book_id: str, chapter_slug: str) -> Response:
    """Render one sanitized, reflowable chapter with ordered navigation."""

    catalog = BookCatalog(request.app.state.settings.published_content_dir)
    try:
        book = catalog.load_book(book_id)
        selected_chapter = book.chapter_by_slug(chapter_slug)
        markdown = catalog.load_chapter_markdown(book, selected_chapter)
    except (FileNotFoundError, KeyError, OSError) as error:
        raise HTTPException(status_code=404, detail="Chapter not found") from error

    position = book.chapter_position(selected_chapter)
    previous_chapter = book.chapters[position - 1] if position > 0 else None
    next_chapter = (
        book.chapters[position + 1] if position + 1 < book.chapter_count else None
    )
    source_lookup = {source.id: source for source in book.sources}
    sources = [source_lookup[source_id] for source_id in selected_chapter.source_ids]

    return templates.TemplateResponse(
        request=request,
        name="chapter.html",
        context={
            "book": book,
            "chapter": selected_chapter,
            "domain": domain_for_chapter(book, selected_chapter),
            "chapter_html": Markup(render_markdown(markdown)),
            "chapter_number": position + 1,
            "previous_chapter": previous_chapter,
            "next_chapter": next_chapter,
            "sources": sources,
        },
    )


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    """Report public process readiness without exposing configuration."""

    status = "ok" if request.app.state.ready else "starting"
    return {"service": "reader", "status": status}
