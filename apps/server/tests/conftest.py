import os
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from pydantic import SecretStr

from fource.common import Settings
from fource.db import Database
from fource.identity import Role, create_user
from fource.server.main import create_app
from fource.server.migrate import upgrade

SECRET = "s" * 40
PASSWORD = "correct horse battery"


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
