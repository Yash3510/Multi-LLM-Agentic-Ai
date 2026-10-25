from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from fource.common import FourceError, Settings
from fource.db import APP_ROLE, Database
from fource.server.errors import install_error_handlers
from fource.server.routes import auth, health

VERSION = "0.1.0"


class UnsafeDatabaseRole(FourceError):
    code = "unsafe_database_role"
    status = 500


def refuse_a_bypassing_role(role: str, *, bypasses: bool) -> None:
    """A superuser or BYPASSRLS role ignores row-level security, so a server connected as one
    (the owner, through a wrong FOURCE_DATABASE_URL) would silently lose the isolation between
    organisations. Refuse to start instead. The message names the role, never the URL."""
    if bypasses:
        raise UnsafeDatabaseRole(
            f"The database role '{role}' is a superuser or bypasses row-level security, "
            "which would switch off the isolation between organisations. "
            f"Connect the server as {APP_ROLE} through FOURCE_DATABASE_URL."
        )


async def check_database_role(database: Database) -> None:
    """On PostgreSQL, asks the server's own role whether it bypasses row-level security.
    SQLite has no roles."""
    if database.engine.dialect.name != "postgresql":
        return
    async with database.engine.connect() as connection:
        row = (
            await connection.execute(
                text(
                    "SELECT current_user, rolsuper OR rolbypassrls"
                    " FROM pg_roles WHERE rolname = current_user"
                )
            )
        ).one()
    refuse_a_bypassing_role(row[0], bypasses=row[1])


def create_app(settings: Settings) -> FastAPI:
    """The 4CE API. The engine is created here and closed on shutdown. On PostgreSQL the lifespan
    connects at start-up to check the role, so an unreachable database fails start-up.

    The Swagger and ReDoc pages are off: they load assets from a CDN, and 4CE runs offline.
    """
    database = Database(settings.database_url.get_secret_value())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        try:
            await check_database_role(database)
            yield
        finally:
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
