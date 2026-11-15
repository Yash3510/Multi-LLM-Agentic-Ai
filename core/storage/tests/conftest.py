import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from fource.db import Base, Database, Org
from fource.storage import Blobs, LocalBlobs


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


@pytest.fixture(params=["local"])
async def blobs(request: pytest.FixtureRequest, tmp_path: Path) -> AsyncIterator[Blobs]:
    """The same contract on every adapter: a folder here, and (from the S3 adapter on) MinIO
    in the `minio` runs."""
    store = LocalBlobs(tmp_path / "files")
    try:
        yield store
    finally:
        await store.close()
