import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from fource.db import Base, Database, Org
from fource.storage import Blobs, LocalBlobs, S3Blobs, make_s3_client

NEEDS_MINIO = (
    "MinIO tests need FOURCE_TEST_S3_ENDPOINT, FOURCE_TEST_S3_ACCESS_KEY and "
    "FOURCE_TEST_S3_SECRET_KEY: a MinIO these tests may write to (CI's MinIO job sets them). "
    "Never point them at a shared server."
)


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


async def minio_blobs() -> S3Blobs:
    """A fresh bucket on the MinIO the FOURCE_TEST_S3_* variables name: read from the
    environment only, never .env; a missing variable fails the test, it never skips."""
    names = ("FOURCE_TEST_S3_ENDPOINT", "FOURCE_TEST_S3_ACCESS_KEY", "FOURCE_TEST_S3_SECRET_KEY")
    endpoint, access_key, secret_key = (os.environ.get(name, "") for name in names)
    if not (endpoint and access_key and secret_key):
        pytest.fail(NEEDS_MINIO)
    client = make_s3_client(
        endpoint, access_key=access_key, secret_key=secret_key, region="us-east-1"
    )
    blobs = S3Blobs(client, f"fource-test-{uuid.uuid4().hex[:12]}")
    assert await blobs.create_bucket()
    return blobs


@pytest.fixture(params=["local", pytest.param("minio", marks=pytest.mark.minio)])
async def blobs(request: pytest.FixtureRequest, tmp_path: Path) -> AsyncIterator[Blobs]:
    """The same contract on every adapter: a folder here everywhere, and a real MinIO in the
    `minio` runs (`just test-minio`, CI's MinIO job)."""
    store: Blobs = (
        LocalBlobs(tmp_path / "files") if request.param == "local" else await minio_blobs()
    )
    try:
        yield store
    finally:
        await store.close()
