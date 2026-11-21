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


def server() -> tuple[str, str, str]:
    names = ("FOURCE_TEST_S3_ENDPOINT", "FOURCE_TEST_S3_ACCESS_KEY", "FOURCE_TEST_S3_SECRET_KEY")
    endpoint, access_key, secret_key = (os.environ.get(name, "") for name in names)
    if not (endpoint and access_key and secret_key):
        pytest.fail("MinIO tests need the FOURCE_TEST_S3_* variables (see conftest.py).")
    return endpoint, access_key, secret_key


async def fresh_bucket() -> S3Blobs:
    endpoint, access_key, secret_key = server()
    client = make_s3_client(
        endpoint, access_key=access_key, secret_key=secret_key, region="us-east-1"
    )
    blobs = S3Blobs(client, f"fource-test-{uuid.uuid4().hex[:12]}")
    assert await blobs.create_bucket()
    return blobs


async def test_more_than_a_part_goes_up_in_parts_and_reads_back() -> None:
    blobs = await fresh_bucket()
    data = os.urandom(PART + 12_345)  # two parts: 8 MiB, then the rest
    at = BlobKey(uuid.uuid4(), uuid.uuid4())
    await blobs.write(at, source(data[:3_000_000], data[3_000_000:]))
    assert await read_all(blobs, at) == data
    await blobs.close()


async def test_creating_the_bucket_again_changes_nothing() -> None:
    blobs = await fresh_bucket()
    assert not await blobs.create_bucket()
    assert await blobs.ping()
    await blobs.close()


async def test_the_server_refuses_a_body_changed_after_signing() -> None:
    # The signature covers the body's SHA-256; a body changed on the way must not be stored.
    blobs = await fresh_bucket()
    endpoint, access_key, secret_key = server()
    client = make_s3_client(
        endpoint, access_key=access_key, secret_key=secret_key, region="us-east-1"
    )

    def change_the_body(request: AWSRequest, operation_name: str, **kwargs: object) -> None:
        if operation_name == "PutObject":
            request.data = b"changed after signing"

    # Registered last on the signer's own event, so it runs after the signature is made.
    client.meta.events.register_last("request-created.s3", change_the_body)
    tampered = S3Blobs(client, blobs.bucket)
    at = BlobKey(uuid.uuid4(), uuid.uuid4())
    with pytest.raises(StorageUnavailable):
        await tampered.write(at, source(b"the body that was signed"))
    with pytest.raises(BlobMissing):
        await read_all(blobs, at)
    await blobs.close()
    await tampered.close()
