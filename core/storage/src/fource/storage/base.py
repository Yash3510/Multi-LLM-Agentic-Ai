"""The adapter seam of file storage: where the bytes live (ADR-0044)."""

from collections.abc import AsyncIterable, AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Protocol

from fource.storage.keys import BlobKey

CHUNK_SIZE = 64 * 1024


class Blobs(Protocol):
    """Bytes by key. Nothing here knows about records, sizes or hashes: the storage service
    does. Adapters raise StorageUnavailable when the store can't be used."""

    backend: str

    async def write(self, key: BlobKey, chunks: AsyncIterable[bytes]) -> None:
        """Stores every chunk under the key, or nothing: if the source raises or the call is
        cancelled, no part of the bytes stays behind."""
        ...

    def read(self, key: BlobKey) -> AbstractAsyncContextManager[AsyncIterator[bytes]]:
        """The key's bytes in chunks; BlobMissing when the key has none."""
        ...

    async def delete(self, key: BlobKey) -> None:
        """Removes the key's bytes; a key without any is fine."""
        ...

    async def ping(self) -> bool: ...

    async def close(self) -> None: ...
