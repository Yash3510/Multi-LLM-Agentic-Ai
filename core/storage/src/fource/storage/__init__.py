"""Files per organisation: the storage interface, its adapters and the records (ADR-0044)."""

from typing import TYPE_CHECKING

from fource.common import Settings
from fource.storage.base import CHUNK_SIZE, Blobs
from fource.storage.errors import (
    BlobMissing,
    FileDamaged,
    FileNotFound,
    FileTooLarge,
    StorageUnavailable,
)
from fource.storage.keys import BlobKey
from fource.storage.local import LocalBlobs
from fource.storage.models import StoredFile
from fource.storage.service import ERASE, FileInfo, Reading, Storage, erase_handler

if TYPE_CHECKING:
    from fource.storage.s3 import S3Blobs, make_s3_client


def __getattr__(name: str) -> object:
    """The S3 names load boto3, so their module is imported only when one is asked for."""
    if name in _S3_NAMES:
        from fource.storage import s3

        return getattr(s3, name)
    raise AttributeError(f"module 'fource.storage' has no attribute {name!r}")


_S3_NAMES = ("S3Blobs", "make_s3_client")


def open_storage(settings: Settings) -> Storage:
    """The file store FOURCE_STORAGE names: `<FOURCE_DATA_DIR>/files`, or the S3 bucket. boto3
    is imported only for the second."""
    max_bytes = settings.storage_max_file_mb * 1024 * 1024
    if settings.storage == "local":
        return Storage(LocalBlobs(settings.data_dir / "files"), max_bytes=max_bytes)
    from fource.storage.s3 import PROBE_SECONDS, S3Blobs, make_s3_client

    endpoint, access_key, secret = (
        settings.s3_endpoint,
        settings.s3_access_key,
        settings.s3_secret_key,
    )
    if endpoint is None or access_key is None or secret is None:  # Settings refuses this first
        raise ValueError("FOURCE_STORAGE=s3 needs FOURCE_S3_ENDPOINT and both FOURCE_S3_*_KEY")
    client = make_s3_client(
        endpoint,
        access_key=access_key,
        secret_key=secret.get_secret_value(),
        region=settings.s3_region,
    )
    probe = make_s3_client(  # for health: one short try, never the data client's retries
        endpoint,
        access_key=access_key,
        secret_key=secret.get_secret_value(),
        region=settings.s3_region,
        connect_timeout=PROBE_SECONDS,
        read_timeout=PROBE_SECONDS,
        attempts=1,
    )
    return Storage(S3Blobs(client, settings.s3_bucket, probe=probe), max_bytes=max_bytes)


__all__ = [
    "CHUNK_SIZE",
    "ERASE",
    "BlobKey",
    "BlobMissing",
    "Blobs",
    "FileDamaged",
    "FileInfo",
    "FileNotFound",
    "FileTooLarge",
    "LocalBlobs",
    "Reading",
    "S3Blobs",
    "Storage",
    "StorageUnavailable",
    "StoredFile",
    "make_s3_client",
    "erase_handler",
    "open_storage",
]
