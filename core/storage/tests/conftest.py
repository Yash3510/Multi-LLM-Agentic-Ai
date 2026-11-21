import os
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio.to_thread
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


def minio_credentials() -> tuple[str, str, str]:
    """The MinIO the FOURCE_TEST_S3_* variables name: read from the environment only, never
    .env; a missing variable fails the test, it never skips."""
    names = ("FOURCE_TEST_S3_ENDPOINT", "FOURCE_TEST_S3_ACCESS_KEY", "FOURCE_TEST_S3_SECRET_KEY")
    endpoint, access_key, secret_key = (os.environ.get(name, "") for name in names)
    if not (endpoint and access_key and secret_key):
        pytest.fail(NEEDS_MINIO)
    return endpoint, access_key, secret_key


@asynccontextmanager
async def minio_bucket() -> AsyncGenerator[S3Blobs]:
    """A fresh bucket on that MinIO, emptied and removed again whatever the test did, so a
    MinIO that outlives the run (CI's service, a developer's) does not fill up."""
    endpoint, access_key, secret_key = minio_credentials()
    client = make_s3_client(
        endpoint, access_key=access_key, secret_key=secret_key, region="us-east-1"
    )
    store = S3Blobs(client, f"fource-test-{uuid.uuid4().hex[:12]}")

    def remove_bucket() -> None:
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=store.bucket):
            for item in page.get("Contents", []):
                if "Key" in item:
                    client.delete_object(Bucket=store.bucket, Key=item["Key"])
        for unfinished in client.list_multipart_uploads(Bucket=store.bucket).get("Uploads", []):
            if "Key" in unfinished and "UploadId" in unfinished:
                client.abort_multipart_upload(
                    Bucket=store.bucket, Key=unfinished["Key"], UploadId=unfinished["UploadId"]
                )
        client.delete_bucket(Bucket=store.bucket)

    try:
        assert await store.create_bucket()
        try:
            yield store
        finally:
            await anyio.to_thread.run_sync(remove_bucket)
    finally:
        await store.close()


@pytest.fixture
def minio_server() -> tuple[str, str, str]:
    return minio_credentials()


@pytest.fixture
async def minio_store() -> AsyncIterator[S3Blobs]:
    async with minio_bucket() as store:
        yield store


@pytest.fixture(params=["local", pytest.param("minio", marks=pytest.mark.minio)])
async def blobs(request: pytest.FixtureRequest, tmp_path: Path) -> AsyncIterator[Blobs]:
    """The same contract on every adapter: a folder here everywhere, and a real MinIO in the
    `minio` runs (`just test-minio`, CI's MinIO job)."""
    if request.param == "local":
        local = LocalBlobs(tmp_path / "files")
        try:
            yield local
        finally:
            await local.close()
    else:
        async with minio_bucket() as store:
            yield store
