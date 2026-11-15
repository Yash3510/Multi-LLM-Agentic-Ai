import uuid
from collections.abc import AsyncIterator

import pytest

from fource.storage import BlobKey, BlobMissing, Blobs

pytestmark = pytest.mark.anyio
FIRST = uuid.UUID("0190a0b1-0000-7000-8000-000000000001")
SECOND = uuid.UUID("0190a0b1-0000-7000-8000-000000000002")


def key(org: uuid.UUID = FIRST) -> BlobKey:
    return BlobKey(org, uuid.uuid4())


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def failing_source() -> AsyncIterator[bytes]:
    yield b"half of it"
    raise ValueError("the upload broke off")


async def read_all(blobs: Blobs, at: BlobKey) -> bytes:
    async with blobs.read(at) as chunks:
        return b"".join([chunk async for chunk in chunks])


async def test_bytes_written_in_many_chunks_read_back_the_same(blobs: Blobs) -> None:
    at = key()
    parts = [bytes([n]) * 70_000 for n in range(5)]  # more than one read chunk each
    await blobs.write(at, source(*parts))
    assert await read_all(blobs, at) == b"".join(parts)


async def test_an_empty_blob_is_a_blob(blobs: Blobs) -> None:
    at = key()
    await blobs.write(at, source())
    assert await read_all(blobs, at) == b""


async def test_a_key_without_bytes_is_missing(blobs: Blobs) -> None:
    with pytest.raises(BlobMissing):
        await read_all(blobs, key())
    with pytest.raises(BlobMissing):
        await read_all(blobs, key(uuid.uuid4()))  # an organisation never written to


async def test_delete_removes_the_bytes_and_may_be_repeated(blobs: Blobs) -> None:
    at = key()
    await blobs.write(at, source(b"x"))
    await blobs.delete(at)
    await blobs.delete(at)
    await blobs.delete(key(uuid.uuid4()))
    with pytest.raises(BlobMissing):
        await read_all(blobs, at)


async def test_a_failing_source_leaves_nothing(blobs: Blobs) -> None:
    at = key()
    with pytest.raises(ValueError, match="broke off"):
        await blobs.write(at, failing_source())
    with pytest.raises(BlobMissing):
        await read_all(blobs, at)


async def test_the_same_file_id_in_two_organisations_is_two_blobs(blobs: Blobs) -> None:
    file = uuid.uuid4()
    await blobs.write(BlobKey(FIRST, file), source(b"first"))
    await blobs.write(BlobKey(SECOND, file), source(b"second"))
    assert await read_all(blobs, BlobKey(FIRST, file)) == b"first"
    assert await read_all(blobs, BlobKey(SECOND, file)) == b"second"


async def test_a_working_store_answers_ping(blobs: Blobs) -> None:
    assert await blobs.ping()
