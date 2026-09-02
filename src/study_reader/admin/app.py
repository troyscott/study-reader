"""Private administration application factory."""

from fastapi import FastAPI

from study_reader.admin.routes import router
from study_reader.config import Settings, get_settings
from study_reader.lifecycle import build_lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the private administration application."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Study Reader Administration",
        lifespan=build_lifespan(resolved_settings),
    )
    app.include_router(router)
    return app
