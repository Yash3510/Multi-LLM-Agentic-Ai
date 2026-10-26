import os
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Connection, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError

from fource.common import Settings
from fource.db import APP_ROLE, Database
from fource.identity import Role, create_user
from fource.server.main import create_app
from fource.server.migrate import upgrade

SECRET = "s" * 40
PASSWORD = "correct horse battery"
RUN_SERVICES = "PostgreSQL tests need the bundled services: run `just services`"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    """A migrated SQLite database of its own. Sync on purpose: migrations run their own
    event loop, which can't start inside the test's."""
    monkeypatch.chdir(tmp_path)  # no .env from the repository
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)  # nor anything set in the developer's shell
    url = f"sqlite+aiosqlite:///{(tmp_path / 'fource.db').as_posix()}"
    upgrade(url)
    return Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(url))


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """The app with one Admin, ada@example.com. The in-process transport sends no lifespan
    events, so the engine is closed here."""
    app = create_app(settings)
    database: Database = app.state.database
    org_id = await database.org_id(settings.org)
    assert org_id is not None
    async with database.org_session(org_id) as session:
        await create_user(session, email="ada@example.com", password=PASSWORD, roles=[Role.ADMIN])
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await database.dispose()


class _Services(BaseSettings):
    """The bundled services' passwords, read like `just services` reads them."""

    model_config = SettingsConfigDict(env_prefix="FOURCE_", env_file=".env", extra="ignore")
    postgres_password: SecretStr | None = None
    postgres_app_password: SecretStr | None = None
    test_postgres_port: int = Field(default=5432, ge=1, le=65535)


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _ensure_app_role(connection: Connection, password: str) -> None:
    """A data volume created before deploy/config/postgres/10-app-role.sh has no app role."""
    found = connection.exec_driver_sql("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_ROLE,))
    if found.scalar() is None:
        connection.exec_driver_sql(
            f"CREATE ROLE {APP_ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS "
            f"PASSWORD {_literal(password)}"
        )


@pytest.fixture
def postgres() -> Iterator[tuple[str, str]]:
    """A throwaway PostgreSQL database for one test: (owner URL, app-role URL)."""
    services = _Services()
    if services.postgres_password is None or services.postgres_app_password is None:
        pytest.fail(
            f"{RUN_SERVICES}, with FOURCE_POSTGRES_PASSWORD and "
            "FOURCE_POSTGRES_APP_PASSWORD in .env."
        )
    admin = URL.create(
        "postgresql+psycopg",
        username="fource",
        password=services.postgres_password.get_secret_value(),
        host="localhost",
        port=services.test_postgres_port,
        database="fource",
    )
    app_password = services.postgres_app_password.get_secret_value()
    name = f"fource_test_{uuid.uuid4().hex[:12]}"
    engine = create_engine(admin, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            _ensure_app_role(connection, app_password)
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
    except OperationalError as error:
        engine.dispose()
        port = services.test_postgres_port
        pytest.fail(f"{RUN_SERVICES}; PostgreSQL on localhost:{port} said: {error.orig}")
    owner = admin.set(database=name)
    app = owner.set(username=APP_ROLE, password=app_password)
    yield owner.render_as_string(hide_password=False), app.render_as_string(hide_password=False)
    with engine.connect() as connection:
        connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
    engine.dispose()
