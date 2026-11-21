import os
import uuid
from collections.abc import AsyncIterator

import pytest
from botocore.awsrequest import AWSRequest

from fource.storage import BlobKey, BlobMissing, S3Blobs, StorageUnavailable, make_s3_client

pytestmark = [pytest.mark.minio, pytest.mark.anyio]
PART = 8 * 1024 * 1024


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def read_all(blobs: S3Blobs, at: BlobKey) -> bytes:
    async with blobs.read(at) as chunks:
        return b"".join([chunk async for chunk in chunks])


async def test_more_than_a_part_goes_up_in_parts_and_reads_back(minio_store: S3Blobs) -> None:
    blobs = minio_store
    data = os.urandom(PART + 12_345)  # two parts: 8 MiB, then the rest
    at = BlobKey(uuid.uuid4(), uuid.uuid4())
    await blobs.write(at, source(data[:3_000_000], data[3_000_000:]))
    assert await read_all(blobs, at) == data


async def test_creating_the_bucket_again_changes_nothing(minio_store: S3Blobs) -> None:
    assert not await minio_store.create_bucket()
    assert await minio_store.ping()


async def test_the_server_refuses_a_body_changed_after_signing(
    minio_store: S3Blobs, minio_server: tuple[str, str, str]
) -> None:
    # The signature covers the body's SHA-256; a body changed on the way must not be stored.
    endpoint, access_key, secret_key = minio_server
    client = make_s3_client(
        endpoint, access_key=access_key, secret_key=secret_key, region="us-east-1"
    )

    def change_the_body(request: AWSRequest, operation_name: str, **kwargs: object) -> None:
        if operation_name == "PutObject":
            request.data = b"changed after signing"

    # Registered last on the signer's own event, so it runs after the signature is made.
    client.meta.events.register_last("request-created.s3", change_the_body)
    tampered = S3Blobs(client, minio_store.bucket)
    at = BlobKey(uuid.uuid4(), uuid.uuid4())
    try:
        with pytest.raises(StorageUnavailable):
            await tampered.write(at, source(b"the body that was signed"))
        with pytest.raises(BlobMissing):
            await read_all(minio_store, at)
    finally:
        await tampered.close()
