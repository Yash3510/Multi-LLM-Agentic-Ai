from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fource.common import Settings
from fource.db import Database
from fource.server.errors import install_error_handlers
from fource.server.routes import auth, health

VERSION = "0.1.0"


def create_app(settings: Settings) -> FastAPI:
    """The 4CE API. The engine is created here (it connects lazily) and closed on shutdown.

    The Swagger and ReDoc pages are off: they load assets from a CDN, and 4CE runs offline.
    """
    database = Database(settings.database_url.get_secret_value())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        yield
        await database.dispose()

    app = FastAPI(
        title="4CE",
        version=VERSION,
        lifespan=lifespan,
        openapi_url="/api/openapi.json",
        docs_url=None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.database = database
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    return app


def app_factory() -> FastAPI:
    """What Uvicorn calls: settings from the environment and .env."""
    return create_app(Settings())
