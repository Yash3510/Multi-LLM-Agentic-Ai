import hashlib
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.db import Database
from fource.ledger import EntryType, read_entries
from fource.storage import (
    FileDamaged,
    FileNotFound,
    FileTooLarge,
    LocalBlobs,
    Storage,
    StoredFile,
)

pytestmark = pytest.mark.anyio
DATA = b"the quick brown fox " * 10_000  # 200 kB: several read chunks
ACTOR = "user:0190a0b1-0000-7000-8000-00000000000a"


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


def storage_in(tmp_path: Path, max_bytes: int = 10_000_000) -> Storage:
    return Storage(LocalBlobs(tmp_path / "files"), max_bytes=max_bytes)


async def stored_bytes(tmp_path: Path) -> list[Path]:
    return [path for path in (tmp_path / "files").rglob("*") if path.is_file()]


async def test_a_file_is_recorded_with_its_size_hash_and_actor(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session,
            source(DATA[:5], DATA[5:]),
            name="notes.txt",
            content_type="text/plain",
            actor=ACTOR,
        )
    assert (info.name, info.size, info.created_by) == ("notes.txt", len(DATA), ACTOR)
    assert info.sha256 == hashlib.sha256(DATA).hexdigest()
    async with database.org_session(first) as session:
        assert await storage.stat(session, info.id) == info


async def test_a_put_writes_one_file_write_entry_without_the_name(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    async with database.org_session(first) as session:
        info = await storage_in(tmp_path).put(
            session, source(DATA), name="private name.txt", content_type="text/plain", actor=ACTOR
        )
    async with database.org_session(first) as session:
        entries = [entry async for entry in read_entries(session)]
    assert [entry.type for entry in entries] == [EntryType.FILE_WRITE]
    entry = entries[0]
    assert (entry.actor, entry.outputs_sha256, entry.inputs_sha256) == (ACTOR, info.sha256, None)
    assert dict(entry.refs) == {
        "file": str(info.id),
        "size": str(len(DATA)),
        "content_type": "text/plain",
    }
    assert "private name" not in str(entry.to_dict())


async def test_a_file_over_the_limit_leaves_no_bytes_record_or_entry(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    with pytest.raises(FileTooLarge, match="FOURCE_STORAGE_MAX_FILE_MB"):
        async with database.org_session(first) as session:
            await storage_in(tmp_path, max_bytes=10).put(
                session,
                source(b"123456", b"78901"),
                name="a",
                content_type="text/plain",
                actor=ACTOR,
            )
    async with database.org_session(first) as session:
        assert await session.scalar(select(func.count()).select_from(StoredFile)) == 0
        assert [entry async for entry in read_entries(session)] == []
    assert await stored_bytes(tmp_path) == []


async def test_another_organisations_file_is_not_found(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, second = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(b"x"), name="a", content_type="text/plain", actor=ACTOR
        )
    async with database.org_session(second) as session:
        with pytest.raises(FileNotFound):
            await storage.stat(session, info.id)


async def test_the_organisation_filter_holds_without_the_sessions_confinement(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    # A plain session has no confinement hook (as a Core select would not), so the service's
    # own filter on organisation is the only thing keeping the other organisation's file out.
    database, first, second = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(b"x"), name="a", content_type="text/plain", actor=ACTOR
        )
    async with AsyncSession(database.engine, info={"org_id": second}) as session:
        with pytest.raises(FileNotFound):
            await storage.stat(session, info.id)
    async with AsyncSession(database.engine, info={"org_id": first}) as session:
        assert await storage.stat(session, info.id) == info


async def test_a_deleted_file_is_not_found_like_one_that_never_existed(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(b"x"), name="a", content_type="text/plain", actor=ACTOR
        )
        row = await session.get(StoredFile, info.id)
        assert row is not None
        row.deleted_at = datetime.now(UTC)
    async with database.org_session(first) as session:
        with pytest.raises(FileNotFound, match="There is no such file."):
            await storage.stat(session, info.id)
        with pytest.raises(FileNotFound, match="There is no such file."):
            async with storage.open(session, info.id):
                pass


async def test_a_session_without_an_organisation_is_refused(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    # SQLite has no row-level security behind the session's filter: the service checks itself.
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(b"x"), name="a", content_type="text/plain", actor=ACTOR
        )
    async with database.session() as session:
        with pytest.raises(RuntimeError, match="organisation session"):
            await storage.stat(session, info.id)


@pytest.mark.parametrize(
    ("name", "content_type"),
    [
        ("", "text/plain"),
        ("a\x00b", "text/plain"),
        ("n" * 256, "text/plain"),
        ("a", "Text/Plain"),
        ("a", "text"),
    ],
)
async def test_a_bad_name_or_type_is_refused_before_any_byte_moves(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path, name: str, content_type: str
) -> None:
    database, first, _ = orgs
    with pytest.raises(ValueError):
        async with database.org_session(first) as session:
            await storage_in(tmp_path).put(
                session, source(b"x"), name=name, content_type=content_type, actor=ACTOR
            )
    assert not (tmp_path / "files").exists()


async def test_a_file_comes_back_checked(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, second = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(DATA), name="notes.txt", content_type="text/plain", actor=ACTOR
        )
    async with database.org_session(first) as session:
        async with storage.open(session, info.id) as reading:
            assert reading.file == info
            assert b"".join([chunk async for chunk in reading]) == DATA
    async with database.org_session(second) as session:
        with pytest.raises(FileNotFound):
            async with storage.open(session, info.id):
                pass
    async with database.session() as session:
        with pytest.raises(RuntimeError, match="organisation session"):
            async with storage.open(session, info.id):
                pass


async def test_changed_or_missing_bytes_are_reported_as_damaged(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(DATA), name="a", content_type="text/plain", actor=ACTOR
        )
    (path,) = await stored_bytes(tmp_path)
    path.write_bytes(DATA[:-1] + b"!")  # same size, other bytes
    async with database.org_session(first) as session:
        with pytest.raises(FileDamaged):
            async with storage.open(session, info.id) as reading:
                async for _ in reading:
                    pass
    path.unlink()
    async with database.org_session(first) as session:
        with pytest.raises(FileDamaged, match="missing"):
            async with storage.open(session, info.id):
                pass


async def test_a_blob_longer_than_its_record_stops_at_the_recorded_size(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(DATA), name="a", content_type="text/plain", actor=ACTOR
        )
    (path,) = await stored_bytes(tmp_path)
    path.write_bytes(DATA + DATA)  # appended: the same start, then more
    delivered = 0
    async with database.org_session(first) as session:
        with pytest.raises(FileDamaged):
            async with storage.open(session, info.id) as reading:
                async for chunk in reading:
                    delivered += len(chunk)
    assert delivered <= info.size


async def test_a_reading_is_read_once(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    storage = storage_in(tmp_path)
    async with database.org_session(first) as session:
        info = await storage.put(
            session, source(DATA), name="a", content_type="text/plain", actor=ACTOR
        )
    async with database.org_session(first) as session:
        async with storage.open(session, info.id) as reading:
            assert b"".join([chunk async for chunk in reading]) == DATA
            with pytest.raises(RuntimeError, match="a Reading is read once"):
                async for _ in reading:
                    pass


@pytest.mark.parametrize(
    ("max_bytes", "said", "not_said"),
    [
        (10, "at most 10 bytes", "0 MiB"),
        (1_500_000, "at most 1500000 bytes", "1 MiB"),
        (2 * 1024 * 1024, "at most 2 MiB", "bytes"),
    ],
)
async def test_the_limit_is_named_in_the_unit_that_states_it_exactly(
    orgs: tuple[Database, uuid.UUID, uuid.UUID],
    tmp_path: Path,
    max_bytes: int,
    said: str,
    not_said: str,
) -> None:
    database, first, _ = orgs
    with pytest.raises(FileTooLarge) as caught:
        async with database.org_session(first) as session:
            await storage_in(tmp_path, max_bytes=max_bytes).put(
                session,
                source(b"x" * (max_bytes + 1)),
                name="a",
                content_type="text/plain",
                actor=ACTOR,
            )
    assert said in str(caught.value)
    assert not_said not in str(caught.value)
