import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from fource.common import set_clock
from fource.db import Base, Database, Org

START = datetime(2026, 11, 14, 10, 0, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class Clock:
    """The time every 4CE package reads (fource.common.now), moved by hand."""

    def __init__(self) -> None:
        self.current = START

    def __call__(self) -> datetime:
        return self.current

    def advance(self, by: timedelta) -> None:
        self.current += by


@pytest.fixture
def clock() -> Iterator[Clock]:
    moved = Clock()
    set_clock(moved)
    yield moved
    set_clock(None)


@pytest.fixture
async def orgs(tmp_path: Path) -> AsyncIterator[tuple[Database, uuid.UUID, uuid.UUID]]:
    """A SQLite database with every table and two organisations."""
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'jobs.db').as_posix()}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    first, second = Org(slug="first", name="First"), Org(slug="second", name="Second")
    async with database.session() as session:
        session.add_all([first, second])
        await session.commit()
    yield database, first.id, second.id
    await database.dispose()
