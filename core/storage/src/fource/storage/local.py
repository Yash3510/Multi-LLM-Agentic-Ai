"""Bytes in a folder on this machine: development and single-machine installs (ADR-0044)."""

import os
import secrets
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import BinaryIO

import anyio.to_thread

from fource.storage.base import CHUNK_SIZE
from fource.storage.errors import BlobMissing, StorageUnavailable
from fource.storage.keys import BlobKey

_BINARY = getattr(os, "O_BINARY", 0)  # Windows: no newline translation


async def _io[*Args, Result](function: Callable[[*Args], Result], *args: *Args) -> Result:
    """Runs blocking file work in a worker thread; an OS error becomes StorageUnavailable,
    whose message names the problem, never the path."""
    try:
        return await anyio.to_thread.run_sync(function, *args)
    except OSError as error:
        raise StorageUnavailable(
            f"The file store could not be used ({error.strerror or type(error).__name__})."
        ) from None


def _create(part: Path) -> BinaryIO:
    descriptor = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _BINARY, 0o600)
    return os.fdopen(descriptor, "wb")


def _sync_folder(folder: Path) -> None:
    """Makes the rename itself durable. POSIX only: Windows can't open a folder this way."""
    if os.name == "posix":
        descriptor = os.open(folder, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _publish(handle: BinaryIO, part: Path, final: Path) -> None:
    handle.flush()
    os.fsync(handle.fileno())
    handle.close()
    os.replace(part, final)
    _sync_folder(final.parent)


def _discard(handle: BinaryIO, part: Path) -> None:
    """Cleans up after a failed or cancelled write, without awaiting (so a cancellation can't
    interrupt it) and without hiding the error that got us here."""
    try:
        handle.close()
    except OSError:
        pass
    try:
        part.unlink(missing_ok=True)
    except OSError:
        pass


async def _chunks(handle: BinaryIO) -> AsyncIterator[bytes]:
    while chunk := await _io(handle.read, CHUNK_SIZE):
        yield chunk


class LocalBlobs:
    """Each key is the file `<root>/<org hex>/<file hex>`. A write goes to a hidden part file
    beside it (created exclusively, owner-only), is synced, then renamed into place, so a
    reader sees the whole file or none."""

    backend = "local"

    def __init__(self, root: Path) -> None:
        self._root = root

    def _folder(self, key: BlobKey) -> Path:
        return self._root / key.org.hex

    def _ready_folder(self, key: BlobKey) -> Path:
        self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            (self._root / key.org.hex).mkdir(mode=0o700)
        except FileExistsError:
            pass
        return self._folder(key)

    def _open(self, key: BlobKey) -> BinaryIO:
        try:
            descriptor = os.open(self._folder(key) / key.file.hex, os.O_RDONLY | _BINARY)
        except FileNotFoundError:
            raise BlobMissing() from None
        return os.fdopen(descriptor, "rb")

    def _remove(self, key: BlobKey) -> None:
        (self._folder(key) / key.file.hex).unlink(missing_ok=True)

    async def write(self, key: BlobKey, chunks: AsyncIterable[bytes]) -> None:
        folder = await _io(self._ready_folder, key)
        part = folder / f".{key.file.hex}.{secrets.token_hex(8)}.part"
        handle = await _io(_create, part)
        try:
            async for chunk in chunks:
                await _io(handle.write, chunk)
            await _io(_publish, handle, part, folder / key.file.hex)
        except BaseException:
            _discard(handle, part)
            raise

    @asynccontextmanager
    async def read(self, key: BlobKey) -> AsyncGenerator[AsyncIterator[bytes]]:
        handle = await _io(self._open, key)
        try:
            yield _chunks(handle)
        finally:
            handle.close()

    async def delete(self, key: BlobKey) -> None:
        await _io(self._remove, key)

    async def ping(self) -> bool:
        """True when the root exists (or could be made) as a folder 4CE may write to."""
        try:
            await anyio.to_thread.run_sync(
                lambda: self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
            )
        except OSError:
            return False
        return self._root.is_dir() and os.access(self._root, os.W_OK)

    async def close(self) -> None:
        return None
