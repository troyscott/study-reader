"""Routes reserved for the private administration service."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/admin")


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    """Report private administration process readiness."""

    status = "ok" if request.app.state.ready else "starting"
    return {"service": "admin", "status": status}


@router.get("/")
async def dashboard() -> dict[str, str]:
    """Provide a minimal private foundation without enabling mutations yet."""

    return {"service": "admin", "status": "foundation"}
