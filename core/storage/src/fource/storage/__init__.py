"""Files per organisation: the storage interface, its adapters and the records (ADR-0044)."""

from typing import TYPE_CHECKING

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
from fource.storage.service import FileInfo, Reading, Storage

if TYPE_CHECKING:
    from fource.storage.s3 import S3Blobs, make_s3_client


def __getattr__(name: str) -> object:
    """The S3 names load boto3, so their module is imported only when one is asked for."""
    if name in _S3_NAMES:
        from fource.storage import s3

        return getattr(s3, name)
    raise AttributeError(f"module 'fource.storage' has no attribute {name!r}")


_S3_NAMES = ("S3Blobs", "make_s3_client")

__all__ = [
    "CHUNK_SIZE",
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
]
