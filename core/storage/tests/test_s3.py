import uuid
from collections.abc import AsyncIterator, Iterator

import anyio
import pytest
from botocore.stub import Stubber

from fource.storage import BlobKey, S3Blobs, make_s3_client

pytestmark = pytest.mark.anyio
ENDPOINT = "http://127.0.0.1:9"  # never contacted: the Stubber answers every call
SECRET = "stub-secret-value"
AT = BlobKey(uuid.UUID(int=1), uuid.UUID(int=2))
WHERE = {"Bucket": "fource", "Key": AT.path}


@pytest.fixture
def stubbed() -> Iterator[tuple[S3Blobs, Stubber]]:
    client = make_s3_client(ENDPOINT, access_key="stub-key", secret_key=SECRET, region="us-east-1")
    with Stubber(client) as stubber:
        yield S3Blobs(client, "fource", part_size=4), stubber
        stubber.assert_no_pending_responses()


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def test_up_to_one_part_is_one_put(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_response("put_object", {}, {**WHERE, "Body": b"abcd"})
    await blobs.write(AT, source(b"ab", b"cd"))


async def test_more_is_a_multipart_upload_of_whole_parts(
    stubbed: tuple[S3Blobs, Stubber],
) -> None:
    blobs, stubber = stubbed
    upload = {**WHERE, "UploadId": "u1"}
    stubber.add_response("create_multipart_upload", {"UploadId": "u1"}, WHERE)
    for number, body in enumerate([b"abcd", b"efgh", b"ij"], start=1):
        expected = {**upload, "PartNumber": number, "Body": body}
        stubber.add_response("upload_part", {"ETag": f'"e{number}"'}, expected)
    parts = [{"ETag": f'"e{number}"', "PartNumber": number} for number in (1, 2, 3)]
    stubber.add_response(
        "complete_multipart_upload", {}, {**upload, "MultipartUpload": {"Parts": parts}}
    )
    await blobs.write(AT, source(b"abc", b"defgh", b"ij"))


async def test_an_exact_multiple_ends_with_a_full_part(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    upload = {**WHERE, "UploadId": "u1"}
    stubber.add_response("create_multipart_upload", {"UploadId": "u1"}, WHERE)
    for number, body in enumerate([b"abcd", b"efgh"], start=1):
        expected = {**upload, "PartNumber": number, "Body": body}
        stubber.add_response("upload_part", {"ETag": f'"e{number}"'}, expected)
    parts = [{"ETag": '"e1"', "PartNumber": 1}, {"ETag": '"e2"', "PartNumber": 2}]
    stubber.add_response(
        "complete_multipart_upload", {}, {**upload, "MultipartUpload": {"Parts": parts}}
    )
    await blobs.write(AT, source(b"abcd", b"efgh"))


async def test_a_failing_source_aborts_the_upload(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_response("create_multipart_upload", {"UploadId": "u1"}, WHERE)
    stubber.add_response(
        "upload_part",
        {"ETag": '"e1"'},
        {**WHERE, "UploadId": "u1", "PartNumber": 1, "Body": b"abcd"},
    )
    stubber.add_response("abort_multipart_upload", {}, {**WHERE, "UploadId": "u1"})

    async def failing() -> AsyncIterator[bytes]:
        yield b"abcdef"
        raise ValueError("the upload broke off")

    with pytest.raises(ValueError, match="broke off"):
        await blobs.write(AT, failing())


async def test_a_cancelled_upload_is_aborted(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_response("create_multipart_upload", {"UploadId": "u1"}, WHERE)
    stubber.add_response(
        "upload_part",
        {"ETag": '"e1"'},
        {**WHERE, "UploadId": "u1", "PartNumber": 1, "Body": b"abcd"},
    )
    stubber.add_response("abort_multipart_upload", {}, {**WHERE, "UploadId": "u1"})

    async def slow() -> AsyncIterator[bytes]:
        yield b"abcdef"
        await anyio.sleep(30)
        yield b"never sent"

    with anyio.move_on_after(1):  # a slow machine only waits longer
        await blobs.write(AT, slow())
