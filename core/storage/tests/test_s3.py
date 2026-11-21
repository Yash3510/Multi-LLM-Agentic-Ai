import io
import socket
import uuid
from collections.abc import AsyncIterator, Iterator

import anyio
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber
from urllib3.exceptions import SSLError

from fource.storage import BlobKey, BlobMissing, S3Blobs, StorageUnavailable, make_s3_client

pytestmark = pytest.mark.anyio
ENDPOINT = "http://127.0.0.1:9"  # never contacted: the Stubber answers every call
SECRET = "stub-secret-value"
AT = BlobKey(uuid.UUID(int=1), uuid.UUID(int=2))
WHERE = {"Bucket": "fource", "Key": AT.path}


class BrokenTls(io.BytesIO):
    """A body whose TLS stream fails part way, as urllib3 reports a bad record MAC."""

    def read(self, size: int | None = -1, /) -> bytes:
        raise SSLError(f"bad record MAC from {ENDPOINT}")


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


@pytest.mark.parametrize("failing", ["upload_part", "complete_multipart_upload"])
async def test_a_refused_part_or_completion_aborts_the_upload(
    stubbed: tuple[S3Blobs, Stubber], failing: str
) -> None:
    blobs, stubber = stubbed
    upload = {**WHERE, "UploadId": "u1"}
    stubber.add_response("create_multipart_upload", {"UploadId": "u1"}, WHERE)
    first = {**upload, "PartNumber": 1, "Body": b"abcd"}
    if failing == "upload_part":
        stubber.add_client_error("upload_part", "InternalError", expected_params=first)
    else:
        stubber.add_response("upload_part", {"ETag": '"e1"'}, first)
        stubber.add_response(
            "upload_part", {"ETag": '"e2"'}, {**upload, "PartNumber": 2, "Body": b"e"}
        )
        parts = [{"ETag": '"e1"', "PartNumber": 1}, {"ETag": '"e2"', "PartNumber": 2}]
        refused = {**upload, "MultipartUpload": {"Parts": parts}}
        stubber.add_client_error(
            "complete_multipart_upload", "InternalError", expected_params=refused
        )
    stubber.add_response("abort_multipart_upload", {}, upload)
    with pytest.raises(StorageUnavailable):
        await blobs.write(AT, source(b"abcde"))


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


async def test_a_read_streams_the_body_and_closes_it(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    data = bytes(range(256)) * 600  # more than one chunk
    raw = io.BytesIO(data)
    stubber.add_response("get_object", {"Body": StreamingBody(raw, len(data))}, WHERE)
    async with blobs.read(AT) as chunks:
        got = [chunk async for chunk in chunks]
    assert b"".join(got) == data and len(got) > 1
    assert raw.closed


async def test_a_missing_key_is_missing(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_client_error("get_object", "NoSuchKey", http_status_code=404, expected_params=WHERE)
    with pytest.raises(BlobMissing):
        async with blobs.read(AT):
            pass


async def test_a_tls_error_part_way_through_a_body_is_unavailable_and_unnamed(
    stubbed: tuple[S3Blobs, Stubber], caplog: pytest.LogCaptureFixture
) -> None:
    blobs, stubber = stubbed
    stubber.add_response("get_object", {"Body": StreamingBody(BrokenTls(), 10)}, WHERE)
    with pytest.raises(StorageUnavailable, match="can't be reached") as refused:
        async with blobs.read(AT) as chunks:
            _ = [chunk async for chunk in chunks]
    shown = refused.value.message + caplog.text
    assert "SSLError" in caplog.text
    assert ENDPOINT not in shown and "127.0.0.1" not in shown
    assert refused.value.__cause__ is None and refused.value.__suppress_context__


@pytest.mark.parametrize(
    ("code", "status", "says"),
    [
        ("AccessDenied", 403, "FOURCE_S3_ACCESS_KEY"),
        ("SignatureDoesNotMatch", 403, "FOURCE_S3_SECRET_KEY"),
        ("NoSuchBucket", 404, "just migrate"),
        ("InternalError", 500, "refused the request"),
    ],
)
async def test_refusals_become_storage_unavailable_naming_no_endpoint_or_key(
    stubbed: tuple[S3Blobs, Stubber],
    caplog: pytest.LogCaptureFixture,
    code: str,
    status: int,
    says: str,
) -> None:
    blobs, stubber = stubbed
    stubber.add_client_error("put_object", code, f"text naming {ENDPOINT}", http_status_code=status)
    with pytest.raises(StorageUnavailable) as refused:
        await blobs.write(AT, source(b"x"))
    assert says in refused.value.message
    shown = refused.value.message + caplog.text
    assert code in caplog.text
    assert ENDPOINT not in shown and "127.0.0.1" not in shown and SECRET not in shown


async def test_an_unreachable_store_is_unavailable_and_unnamed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with socket.socket() as closed:  # a port nothing listens on any more
        closed.bind(("127.0.0.1", 0))
        endpoint = f"http://127.0.0.1:{closed.getsockname()[1]}"
    client = make_s3_client(endpoint, access_key="k", secret_key=SECRET, region="us-east-1")
    blobs = S3Blobs(client, "fource")
    with pytest.raises(StorageUnavailable, match="can't be reached") as refused:
        await blobs.write(AT, source(b"x"))
    assert not await blobs.ping()
    shown = refused.value.message + caplog.text
    assert endpoint not in shown and SECRET not in shown
    await blobs.close()


async def test_delete_and_ping(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_response("delete_object", {}, WHERE)
    stubber.add_response("head_bucket", {}, {"Bucket": "fource"})
    stubber.add_client_error("head_bucket", "403", http_status_code=403)
    await blobs.delete(AT)
    assert await blobs.ping()
    assert not await blobs.ping()


async def test_ping_asks_its_own_client_once_and_briefly() -> None:
    data = make_s3_client(ENDPOINT, access_key="stub-key", secret_key=SECRET, region="us-east-1")
    probe = make_s3_client(
        ENDPOINT,
        access_key="stub-key",
        secret_key=SECRET,
        region="us-east-1",
        connect_timeout=2,
        read_timeout=2,
        attempts=1,
    )
    config = vars(probe.meta.config)  # botocore-stubs declare none of its options
    assert (config["connect_timeout"], config["read_timeout"], config["retries"]) == (
        2,
        2,
        {"mode": "standard", "total_max_attempts": 1},
    )
    with Stubber(data), Stubber(probe) as quick:  # a call on `data` would fail: nothing stubbed
        quick.add_response("head_bucket", {}, {"Bucket": "fource"})
        assert await S3Blobs(data, "fource", probe=probe).ping()
        quick.assert_no_pending_responses()


async def test_the_bucket_is_created_only_when_missing(stubbed: tuple[S3Blobs, Stubber]) -> None:
    blobs, stubber = stubbed
    stubber.add_client_error("head_bucket", "404", http_status_code=404)
    stubber.add_response("create_bucket", {}, {"Bucket": "fource"})
    stubber.add_response("head_bucket", {}, {"Bucket": "fource"})
    assert await blobs.create_bucket()
    assert not await blobs.create_bucket()
