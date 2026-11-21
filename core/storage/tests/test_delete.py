import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.db import Database
from fource.jobs import Job, Worker
from fource.ledger import EntryType, read_entries
from fource.storage import (
    ERASE,
    FileNotFound,
    LocalBlobs,
    Storage,
    StoredFile,
    erase_handler,
)

pytestmark = pytest.mark.anyio
ACTOR = "user:0190a0b1-0000-7000-8000-00000000000a"


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def stored(
    database: Database, org: uuid.UUID, tmp_path: Path
) -> tuple[Storage, uuid.UUID, Path]:
    storage = Storage(LocalBlobs(tmp_path / "files"), max_bytes=1_000_000)
    async with database.org_session(org) as session:
        info = await storage.put(
            session, source(b"to be erased"), name="a", content_type="text/plain", actor=ACTOR
        )
    return storage, info.id, tmp_path / "files" / org.hex / info.id.hex


async def test_a_deleted_file_is_gone_for_readers_and_its_erasure_is_queued(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage, file_id, path = await stored(database, first, tmp_path)
    async with database.org_session(first) as session:
        await storage.delete(session, file_id, actor=ACTOR)
    async with database.org_session(first) as session:
        with pytest.raises(FileNotFound):
            await storage.stat(session, file_id)
        with pytest.raises(FileNotFound):
            await storage.delete(session, file_id, actor=ACTOR)
        row = await session.scalar(select(StoredFile).where(StoredFile.id == file_id))
        jobs = (await session.scalars(select(Job))).all()
        entries = [entry async for entry in read_entries(session)]
    assert row is not None and row.deleted_by == ACTOR and row.erased_at is None  # kept
    assert [(job.kind, job.key, job.payload, job.max_attempts) for job in jobs] == [
        (ERASE, f"{ERASE}:{file_id}", {"file": str(file_id)}, 30)  # about a day of tries
    ]
    assert [entry.type for entry in entries] == [EntryType.FILE_WRITE, EntryType.FILE_DELETE]
    assert dict(entries[1].refs) == {"file": str(file_id)}
    assert path.exists()  # the bytes go when the worker runs the job


async def test_a_rolled_back_delete_changes_nothing(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage, file_id, path = await stored(database, first, tmp_path)
    with pytest.raises(RuntimeError):
        async with database.org_session(first) as session:
            await storage.delete(session, file_id, actor=ACTOR)
            raise RuntimeError("the caller's transaction fails")
    async with database.org_session(first) as session:
        assert (await storage.stat(session, file_id)).id == file_id
        assert (await session.scalars(select(Job))).all() == []
        assert [entry.type async for entry in read_entries(session)] == [EntryType.FILE_WRITE]
    assert path.exists()


async def test_the_worker_erases_the_bytes_once_and_keeps_the_record(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage, file_id, path = await stored(database, first, tmp_path)
    async with database.org_session(first) as session:
        await storage.delete(session, file_id, actor=ACTOR)
    worker = Worker(database, {ERASE: erase_handler(storage)})
    assert await worker.run_once() == 1
    assert not path.exists()
    async with database.org_session(first) as session:
        row = await session.scalar(select(StoredFile).where(StoredFile.id == file_id))
        assert row is not None and row.erased_at is not None
        assert not await storage.erase(session, file_id)  # again: nothing to do


async def test_erase_leaves_a_file_that_is_not_deleted_alone(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage, file_id, path = await stored(database, first, tmp_path)
    async with database.org_session(first) as session:
        assert not await storage.erase(session, file_id)
    async with database.session() as session:
        with pytest.raises(RuntimeError, match="organisation session"):
            await storage.erase(session, file_id)
    assert path.exists()


async def test_erase_leaves_another_organisations_deleted_file_alone(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, second = orgs
    storage, file_id, path = await stored(database, first, tmp_path)
    async with database.org_session(first) as session:
        await storage.delete(session, file_id, actor=ACTOR)
    # A deleted file, so only an organisation check can refuse it. The organisation session
    # already filters its reads, so erase's own filter shows only in a session without that
    # filter; it must refuse on its own, whatever session it is given.
    async with database.org_session(second) as session:
        assert not await storage.erase(session, file_id)
    async with AsyncSession(database.engine, info={"org_id": second}) as bare:
        assert not await storage.erase(bare, file_id)
    assert path.exists()
    async with database.org_session(first) as session:
        row = await session.scalar(select(StoredFile).where(StoredFile.id == file_id))
        assert row is not None and row.erased_at is None


async def test_of_two_deletes_at_once_only_the_first_counts(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage, file_id, _ = await stored(database, first, tmp_path)
    with pytest.raises(FileNotFound):
        async with database.org_session(first) as late:
            # This session read the file before the other delete committed, as a second delete
            # running at the same time does.
            seen = await late.scalar(select(StoredFile).where(StoredFile.id == file_id))
            assert seen is not None and seen.deleted_at is None
            async with database.org_session(first) as session:
                await storage.delete(session, file_id, actor="system")
            await storage.delete(late, file_id, actor=ACTOR)
    async with database.org_session(first) as session:
        row = await session.scalar(select(StoredFile).where(StoredFile.id == file_id))
        entries = [entry async for entry in read_entries(session)]
    assert row is not None and row.deleted_by == "system"  # the first delete's
    assert [entry.type for entry in entries] == [EntryType.FILE_WRITE, EntryType.FILE_DELETE]
