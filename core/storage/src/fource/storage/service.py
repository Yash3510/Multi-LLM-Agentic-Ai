"""Files per organisation: records, ledger entries and checked reads over an adapter
(ADR-0044). Every method runs in the caller's organisation session; the caller commits."""

import hashlib
import re
import uuid
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import new_id, now
from fource.db import org_of
from fource.jobs import Handler, HeldJob, enqueue
from fource.ledger import EntryType, append
from fource.storage.base import Blobs
from fource.storage.errors import BlobMissing, FileDamaged, FileNotFound, FileTooLarge
from fource.storage.keys import BlobKey
from fource.storage.models import StoredFile

ERASE = "storage.erase"
MAX_NAME_LENGTH = 255
_TOKEN = r"[a-z0-9][a-z0-9!#$&^_.+-]{0,126}"
_CONTENT_TYPE = re.compile(f"{_TOKEN}/{_TOKEN}")
_MIB = 1024 * 1024


@dataclass(frozen=True)
class FileInfo:
    """What 4CE knows about one stored file. `name` is for people only: it is never part of a
    path or a key, and never goes into the ledger."""

    id: uuid.UUID
    name: str
    content_type: str
    size: int
    sha256: str
    created_at: datetime
    created_by: str


def _info(row: StoredFile) -> FileInfo:
    return FileInfo(
        id=row.id,
        name=row.name,
        content_type=row.content_type,
        size=row.size,
        sha256=row.sha256,
        created_at=row.created_at,
        created_by=row.created_by,
    )


def _check(name: str, content_type: str) -> None:
    if not 0 < len(name) <= MAX_NAME_LENGTH or not name.isprintable():
        raise ValueError(f"a file name is 1 to {MAX_NAME_LENGTH} printable characters")
    if not _CONTENT_TYPE.fullmatch(content_type):
        raise ValueError("a content type is a lower-case type/subtype, such as text/plain")


def _limit_text(limit: int) -> str:
    """The limit in MiB when that is exact (open_storage always gives whole MiB), else in bytes."""
    return f"{limit // _MIB} MiB" if limit % _MIB == 0 else f"{limit} bytes"


class _Meter:
    """Counts and hashes the bytes on their way to the adapter, and stops them at the limit
    (the adapter then discards what it had)."""

    def __init__(self, chunks: AsyncIterable[bytes], limit: int) -> None:
        self._chunks = chunks
        self._limit = limit
        self._digest = hashlib.sha256()
        self.size = 0

    async def flow(self) -> AsyncIterator[bytes]:
        async for chunk in self._chunks:
            self.size += len(chunk)
            if self.size > self._limit:
                limit = _limit_text(self._limit)
                raise FileTooLarge(f"A file may be at most {limit} (FOURCE_STORAGE_MAX_FILE_MB).")
            self._digest.update(chunk)
            yield chunk

    @property
    def sha256(self) -> str:
        return self._digest.hexdigest()


class Reading:
    """One file being read: `file` says what it must be, and iterating yields its bytes and then
    checks them against `file`. Chunks before a difference are already delivered, so a caller
    that gets FileDamaged treats the whole read as failed. A Reading is read once."""

    def __init__(self, file: FileInfo, chunks: AsyncIterator[bytes]) -> None:
        self.file = file
        self._chunks = chunks
        self._used = False

    def __aiter__(self) -> AsyncIterator[bytes]:
        if self._used:
            raise RuntimeError("a Reading is read once")
        self._used = True
        return self._read()

    async def _read(self) -> AsyncIterator[bytes]:
        digest, size = hashlib.sha256(), 0
        async for chunk in self._chunks:
            size += len(chunk)
            # Stops a blob longer than its record at the recorded size: the hash below would
            # catch it too, but only after all of it had gone out.
            if size > self.file.size:
                raise FileDamaged("The stored bytes of this file differ from what was written.")
            digest.update(chunk)
            yield chunk
        # The size check is redundant with the hash comparison; it is kept as a cheap guard.
        if size != self.file.size or digest.hexdigest() != self.file.sha256:
            raise FileDamaged("The stored bytes of this file differ from what was written.")


class Storage:
    """Files per organisation over one adapter (`blobs`): a `stored_files` row and a ledger
    entry for every file, reads checked against them, and keys built from ids only."""

    def __init__(self, blobs: Blobs, *, max_bytes: int) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes is a positive number of bytes")
        self.blobs = blobs
        self._max_bytes = max_bytes

    async def put(
        self,
        session: AsyncSession,
        chunks: AsyncIterable[bytes],
        *,
        name: str,
        content_type: str,
        actor: str,
    ) -> FileInfo:
        """Streams the bytes into the store, then records the file and a `file.write` entry
        (its SHA-256, id, size and type; never its name) in the session. Nothing is recorded if
        the bytes don't arrive whole; if the caller rolls back, the bytes stay unreferenced."""
        _check(name, content_type)
        org_id, file_id = org_of(session), new_id()
        meter = _Meter(chunks, self._max_bytes)
        await self.blobs.write(BlobKey(org_id, file_id), meter.flow())
        row = StoredFile(
            id=file_id,
            name=name,
            content_type=content_type,
            size=meter.size,
            sha256=meter.sha256,
            created_by=actor,
        )
        session.add(row)
        await session.flush()
        await append(
            session,
            EntryType.FILE_WRITE,
            actor=actor,
            outputs_sha256=meter.sha256,
            refs={"file": str(file_id), "size": str(meter.size), "content_type": content_type},
        )
        return _info(row)

    async def _row(self, session: AsyncSession, file_id: uuid.UUID) -> StoredFile:
        """The file's row in the session's organisation, if it isn't deleted: another
        organisation's id finds nothing, which is the boundary (§8.2 rule 10). The filter is
        explicit, as the ledger's is, so a session without an organisation is refused and the
        boundary does not rest on the session's confinement alone (a test reads through a
        session that has none)."""
        org_id = org_of(session)
        row = await session.scalar(
            select(StoredFile).where(StoredFile.id == file_id, StoredFile.org_id == org_id)
        )
        if row is None or row.deleted_at is not None:
            raise FileNotFound("There is no such file.")
        return row

    async def stat(self, session: AsyncSession, file_id: uuid.UUID) -> FileInfo:
        return _info(await self._row(session, file_id))

    @asynccontextmanager
    async def open(self, session: AsyncSession, file_id: uuid.UUID) -> AsyncGenerator[Reading]:
        row = await self._row(session, file_id)
        try:
            async with self.blobs.read(BlobKey(row.org_id, row.id)) as chunks:
                yield Reading(_info(row), chunks)
        except BlobMissing:
            raise FileDamaged("The bytes of this file are missing from the file store.") from None

    async def delete(self, session: AsyncSession, file_id: uuid.UUID, *, actor: str) -> None:
        """Marks the file deleted, writes `file.delete` and queues `storage.erase`, all in the
        caller's transaction: reads refuse the file at once, and the worker erases the bytes
        after the caller commits. A rolled-back delete changes nothing. The record stays: the
        ledger holds only hashes, so erasing never touches it (ADR-0044)."""
        # One statement both checks and marks the row: of two deletes at once, the second waits
        # for the first to commit and then finds nothing, so a file is deleted and recorded once.
        marked = await session.execute(
            update(StoredFile)
            .where(
                StoredFile.id == file_id,
                StoredFile.org_id == org_of(session),
                StoredFile.deleted_at.is_(None),
            )
            .values(deleted_at=now(), deleted_by=actor)
            .returning(StoredFile.id)
        )
        if marked.first() is None:
            raise FileNotFound("There is no such file.")
        await append(session, EntryType.FILE_DELETE, actor=actor, refs={"file": str(file_id)})
        # The back-off doubles to an hour, so 30 attempts keep trying for about a day: a store
        # down for maintenance must not leave the bytes behind for good.
        await enqueue(
            session, ERASE, {"file": str(file_id)}, key=f"{ERASE}:{file_id}", max_attempts=30
        )

    async def erase(self, session: AsyncSession, file_id: uuid.UUID) -> bool:
        """Deletes the bytes of a deleted file and marks its record erased; False when there
        was nothing to do, so a repeated job is harmless."""
        org_id = org_of(session)
        row = await session.scalar(
            select(StoredFile).where(StoredFile.id == file_id, StoredFile.org_id == org_id)
        )
        if row is None or row.deleted_at is None or row.erased_at is not None:
            return False
        await self.blobs.delete(BlobKey(row.org_id, row.id))
        row.erased_at = now()
        await session.flush()
        return True

    async def ping(self) -> bool:
        return await self.blobs.ping()

    async def close(self) -> None:
        await self.blobs.close()


def erase_handler(storage: Storage) -> Handler:
    """The worker's handler for `storage.erase` jobs (payload: the file's id)."""

    async def run(session: AsyncSession, job: HeldJob) -> None:
        await storage.erase(session, uuid.UUID(str(job.payload["file"])))

    # Longer than one S3 call with its three attempts (5 s to connect, 60 s to read, each).
    return Handler(run, lease=timedelta(minutes=5))
