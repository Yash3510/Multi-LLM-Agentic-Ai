import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from fource.db import Base, Database, Org


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def orgs(tmp_path: Path) -> AsyncIterator[tuple[Database, uuid.UUID, uuid.UUID]]:
    """A SQLite database with every table and two organisations."""
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'storage.db').as_posix()}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    first, second = Org(slug="first", name="First"), Org(slug="second", name="Second")
    async with database.session() as session:
        session.add_all([first, second])
        await session.commit()
    yield database, first.id, second.id
    await database.dispose()
