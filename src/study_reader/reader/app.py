"""Public reader application factory."""

from fastapi import FastAPI

from study_reader.config import Settings, get_settings
from study_reader.lifecycle import build_lifespan
from study_reader.reader.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the public read-only reader application."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Study Reader",
        lifespan=build_lifespan(resolved_settings),
    )
    app.include_router(router)
    return app
