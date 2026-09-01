"""Shared FastAPI lifecycle behavior."""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from study_reader.config import Settings


def build_lifespan(
    settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Create an application lifespan bound to validated settings."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        app.state.started_at = datetime.now(UTC)
        app.state.ready = True
        yield
        app.state.ready = False

    return lifespan
