"""Bytes in an S3 bucket (MinIO), through boto3 (ADR-0044).

Only this module imports boto3, and the package imports this module lazily, when one of its S3
names is used: a deployment without S3 never loads boto3. The botocore facts relied on here were
checked on 1.44.5 (the locked version) and are listed in docs/architecture/storage.md.
"""

import logging
import os
from collections.abc import AsyncIterable, Callable
from functools import partial
from typing import TYPE_CHECKING

import anyio
import anyio.to_thread
import boto3.session
import botocore.session
from botocore.config import Config
from botocore.configprovider import (
    BOTOCORE_DEFAUT_SESSION_VARIABLES,
    ConfigChainFactory,
    ConstantProvider,
)
from botocore.exceptions import BotoCoreError, ClientError
from botocore.loaders import Loader
from botocore.plugin import PluginContext, reset_plugin_context, set_plugin_context

from fource.storage.errors import BlobMissing, StorageUnavailable
from fource.storage.keys import BlobKey

if TYPE_CHECKING:
    from types_boto3_s3.client import S3Client
    from types_boto3_s3.type_defs import CompletedPartTypeDef

# botocore logs every request's headers, Authorization included, at DEBUG: keep the whole S3
# stack above that, whatever level the root logger is given. urllib3's warnings name the host
# (a full connection pool, a header it can't parse), so it stays above those too.
for _name in ("botocore", "boto3", "s3transfer"):
    logging.getLogger(_name).setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.ERROR)
_log = logging.getLogger("fource.storage")

CONNECT_SECONDS = 5
READ_SECONDS = 60
ATTEMPTS = 3
POOL_CONNECTIONS = 40  # anyio's default thread limit: a connection for each worker thread
PART_SIZE = 8 * 1024 * 1024  # S3 wants at least 5 MiB in every part but the last
_MISSING = frozenset({"NoSuchKey", "NotFound", "404"})
_CREDENTIALS = frozenset({"AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch"})


def _isolated_session() -> botocore.session.Session:
    """A botocore session whose endpoint, credentials, region, CA bundle, proxy, retries,
    checksums, service data and plugins come from nothing but 4CE's settings: no profile, no
    ~/.aws config or credentials file, no data path, no service data from ~/.aws/models, no
    client-side monitoring. Uses botocore's config_store component, the way botocore's own
    session code recommends for changing lookups.

    Some variables still reach botocore, though none changes where a request goes or who signs
    it (checked on botocore 1.44.5): AWS_EXECUTION_ENV adds a user-agent field,
    AWS_LAMBDA_FUNCTION_NAME with _X_AMZN_TRACE_ID adds a trace header, AWS_BEARER_TOKEN_S3 is
    loaded although S3 still signs with Signature Version 4, and SSLKEYLOGFILE makes urllib3
    write TLS keys, as the standard library does."""
    session = botocore.session.Session()
    store = session.get_component("config_store")
    chains = ConfigChainFactory(session=session, environ={})
    for name, (_, _, default, convert) in BOTOCORE_DEFAUT_SESSION_VARIABLES.items():
        chain = chains.create_config_chain(
            instance_name=name, default=default, conversion_func=convert
        )
        store.set_config_provider(name, chain)
    for name in ("config_file", "credentials_file"):
        store.set_config_provider(name, ConstantProvider(os.devnull))
    for name in ("s3", "proxies_config"):
        store.set_config_provider(name, ConstantProvider(None))
    # Set here, not in Config: botocore takes both, but its type stubs don't know the first and
    # mistype the second. "legacy" never asks the instance for its region; configured
    # endpoint URLs could only come from the environment or files, which this session ignores.
    store.set_config_provider("ignore_configured_endpoint_urls", ConstantProvider(True))
    store.set_config_provider("defaults_mode", ConstantProvider("legacy"))
    # The default loader reads ~/.aws/models before botocore's own data, so a file there could
    # replace S3's endpoint rules: read botocore's own data only.
    session.register_component(
        "data_loader",
        Loader(extra_search_paths=[Loader.BUILTIN_DATA_PATH], include_default_search_paths=False),
    )
    return session


def make_s3_client(
    endpoint: str,
    *,
    access_key: str,
    secret_key: str,
    region: str,
    connect_timeout: float = CONNECT_SECONDS,
    read_timeout: float = READ_SECONDS,
    attempts: int = ATTEMPTS,
) -> "S3Client":
    """One S3 client that talks to `endpoint` and nowhere else: explicit credentials (no
    provider chain, no instance metadata), TLS checked against the default trust store, no
    proxy, no plugin, path-style addressing, bounded time and attempts, and every PUT's body
    signed by its SHA-256 (request checksums only where an operation requires one)."""
    config = Config(
        signature_version="s3v4",
        s3={"addressing_style": "path", "payload_signing_enabled": True},
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={"mode": "standard", "total_max_attempts": attempts},
        proxies={},
        use_fips_endpoint=False,
        use_dualstack_endpoint=False,
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        max_pool_connections=POOL_CONNECTIONS,
    )
    session = boto3.session.Session(botocore_session=_isolated_session())
    # Every new client imports the modules BOTOCORE_EXPERIMENTAL__PLUGINS names and hands itself
    # to them; botocore turns that off this way for the clients it creates itself.
    token = set_plugin_context(PluginContext(plugins="DISABLED"))
    try:
        client: S3Client = session.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=True,
            config=config,
        )
    finally:
        reset_plugin_context(token)
    return client


def _refusal(code: str) -> str:
    if code in _CREDENTIALS:
        return (
            "The file store refused 4CE's credentials: check FOURCE_S3_ACCESS_KEY, "
            "FOURCE_S3_SECRET_KEY and FOURCE_S3_REGION."
        )
    if code == "NoSuchBucket":
        return "The file store has no bucket FOURCE_S3_BUCKET: run `just migrate` to create it."
    return "The file store refused the request."


async def _call[*Args, Result](function: Callable[[*Args], Result], *args: *Args) -> Result:
    """One blocking boto3 call in a worker thread, which is never abandoned: anyio waits for
    it with the default `abandon_on_cancel=False` (anyio/to_thread.py:30), shielded from
    cancellation (anyio/_backends/_asyncio.py:2671), so a cancellation that arrives meanwhile
    takes effect when the call returns. botocore's errors become 4CE's; their text names the
    endpoint, so only the S3 error code is logged."""
    try:
        return await anyio.to_thread.run_sync(function, *args)
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "unknown")
        if code in _MISSING:
            raise BlobMissing() from None
        _log.warning("The file store refused a request: %s", code)
        raise StorageUnavailable(_refusal(code)) from None
    except BotoCoreError as error:
        _log.warning("The file store could not be reached: %s", type(error).__name__)
        raise StorageUnavailable("The file store can't be reached.") from None


class S3Blobs:
    """Each key is the object `<org hex>/<file hex>` in one bucket. Up to `part_size` bytes go
    in one put_object; more go part by part (one part in memory at a time) and the upload is
    completed only after the last, or aborted on any failure or cancellation. Every body is
    signed with its SHA-256, which the server checks."""

    backend = "s3"

    def __init__(self, client: "S3Client", bucket: str, *, part_size: int = PART_SIZE) -> None:
        if part_size < 1:
            raise ValueError("part_size is a positive number of bytes")
        self._client = client
        self.bucket = bucket
        self._part_size = part_size

    async def write(self, key: BlobKey, chunks: AsyncIterable[bytes]) -> None:
        buffer = bytearray()
        upload: str | None = None
        parts: list[CompletedPartTypeDef] = []
        try:
            async for chunk in chunks:
                buffer += chunk
                while len(buffer) > self._part_size:
                    if upload is None:
                        upload = await self._start(key)
                    part = bytes(buffer[: self._part_size])
                    parts.append(await self._part(key, upload, len(parts) + 1, part))
                    del buffer[: self._part_size]
            if upload is None:
                put = partial(
                    self._client.put_object, Bucket=self.bucket, Key=key.path, Body=bytes(buffer)
                )
                await _call(put)
            else:
                parts.append(await self._part(key, upload, len(parts) + 1, bytes(buffer)))
                finish = partial(
                    self._client.complete_multipart_upload,
                    Bucket=self.bucket,
                    Key=key.path,
                    UploadId=upload,
                    MultipartUpload={"Parts": parts},
                )
                await _call(finish)
        except BaseException:
            if upload is not None:
                await self._abort(key, upload)
            raise

    async def _start(self, key: BlobKey) -> str:
        start = partial(self._client.create_multipart_upload, Bucket=self.bucket, Key=key.path)
        return (await _call(start))["UploadId"]

    async def _part(
        self, key: BlobKey, upload: str, number: int, data: bytes
    ) -> "CompletedPartTypeDef":
        send = partial(
            self._client.upload_part,
            Bucket=self.bucket,
            Key=key.path,
            UploadId=upload,
            PartNumber=number,
            Body=data,
        )
        return {"ETag": (await _call(send))["ETag"], "PartNumber": number}

    async def _abort(self, key: BlobKey, upload: str) -> None:
        """Shielded, so it runs even while the write is being cancelled. If it fails, the
        store keeps the parts until its own clean-up of unfinished uploads."""
        abort = partial(
            self._client.abort_multipart_upload, Bucket=self.bucket, Key=key.path, UploadId=upload
        )
        with anyio.CancelScope(shield=True):
            try:
                await _call(abort)
            except (StorageUnavailable, BlobMissing):
                _log.warning("An unfinished multipart upload could not be aborted.")

    async def close(self) -> None:
        self._client.close()
