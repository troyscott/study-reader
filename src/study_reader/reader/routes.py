"""Routes exposed by the public reader."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    """Render the initial read-only project status page."""

    title = request.app.title
    return HTMLResponse(
        "<!doctype html><html lang='en'><head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title></head><body><main>"
        "<h1>Study Reader</h1>"
        "<p>The mobile-first reading experience is under construction.</p>"
        "</main></body></html>"
    )


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    """Report public process readiness without exposing configuration."""

    status = "ok" if request.app.state.ready else "starting"
    return {"service": "reader", "status": status}
