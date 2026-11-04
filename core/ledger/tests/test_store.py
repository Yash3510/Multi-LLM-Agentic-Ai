import asyncio
import sqlite3
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import set_clock
from fource.db import Base, Database, Org
from fource.ledger import (
    EmptyLedger,
    Entry,
    EntryType,
    LedgerHead,
    append,
    checkpoint,
    entry_hash,
    read_entries,
    verify_ledger,
)

pytestmark = pytest.mark.anyio
Orgs = tuple[Database, uuid.UUID, uuid.UUID]


@pytest.fixture
async def orgs(tmp_path: Path) -> AsyncIterator[Orgs]:
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'ledger.db').as_posix()}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with database.session() as session:
        first, second = Org(slug="first", name="First"), Org(slug="second", name="Second")
        session.add_all([first, second])
        await session.commit()
    yield database, first.id, second.id
    await database.dispose()


@pytest.fixture
def clock() -> Iterator[None]:
    set_clock(lambda: datetime(2026, 11, 14, 10, 22, 31, 512999, tzinfo=UTC))
    yield
    set_clock(None)


async def write(database: Database, org_id: uuid.UUID, count: int = 1) -> None:
    for _ in range(count):
        async with database.org_session(org_id) as session:
            await append(session, EntryType.SIGNOUT, actor="system", refs={"n": "x"})


async def entries(database: Database, org_id: uuid.UUID) -> list[Entry]:
    async with database.org_session(org_id) as session:
        return [entry async for entry in read_entries(session)]


async def test_entries_count_from_one_and_link_to_the_one_before(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    stored = await entries(database, org_id)
    assert [entry.seq for entry in stored] == [1, 2, 3]
    assert stored[1].prev == stored[0].hash and stored[2].prev == stored[1].hash
    async with database.org_session(org_id) as session:
        assert (await verify_ledger(session)).ok


async def test_an_entry_reads_back_exactly_as_it_was_hashed(orgs: Orgs, clock: None) -> None:
    database, org_id, _ = orgs
    run = uuid.uuid4()
    async with database.org_session(org_id) as session:
        written = await append(
            session,
            EntryType.USER_CREATE,
            actor="system",
            refs={"user": "u"},
            inputs_sha256="a" * 64,
            run_id=run,
        )
    (stored,) = await entries(database, org_id)
    assert stored == written and entry_hash(stored.fields()) == stored.hash
    assert (stored.at, stored.org, stored.run) == (
        "2026-11-14T10:22:31.512Z",
        str(org_id),
        str(run),
    )


async def test_appending_needs_an_organisation_session(orgs: Orgs) -> None:
    database, _, _ = orgs
    async with database.session() as session:
        with pytest.raises(RuntimeError, match="organisation session"):
            await append(session, EntryType.SIGNOUT, actor="system")


async def test_an_entry_rolled_back_with_its_action_leaves_no_gap(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    with pytest.raises(LookupError):
        async with database.org_session(org_id) as session:
            await append(session, EntryType.SIGNOUT, actor="system")
            raise LookupError("the action failed after writing its entry")
    await write(database, org_id)
    assert [entry.seq for entry in await entries(database, org_id)] == [1]


async def test_concurrent_writers_never_share_or_skip_a_number(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    await asyncio.gather(*(write(database, org_id) for _ in range(20)))
    stored = await entries(database, org_id)
    assert [entry.seq for entry in stored] == list(range(1, 21))
    async with database.org_session(org_id) as session:
        assert (await verify_ledger(session)).ok


async def test_each_organisation_has_its_own_chain(orgs: Orgs) -> None:
    database, first, second = orgs
    await write(database, first, 2)
    await write(database, second, 1)
    assert [entry.seq for entry in await entries(database, first)] == [1, 2]
    (only,) = await entries(database, second)
    assert (only.seq, only.org) == (1, str(second))


async def test_a_checkpoint_signs_the_head_and_is_itself_the_next_entry(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    key = Ed25519PrivateKey.generate()
    await write(database, org_id, 2)
    async with database.org_session(org_id) as session:
        signed = await checkpoint(session, key)
    stored = await entries(database, org_id)
    assert (signed.seq, signed.hash) == (2, stored[1].hash)
    assert (
        stored[2].type == EntryType.CHECKPOINT and stored[2].refs["signature"] == signed.signature
    )
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session, public_key=key.public_key(), checkpoints=[signed])
    assert result.complete and result.anchored_seq == 2


async def test_an_empty_ledger_has_nothing_to_checkpoint(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    with pytest.raises(EmptyLedger):
        async with database.org_session(org_id) as session:
            await checkpoint(session, Ed25519PrivateKey.generate())
    await write(database, org_id)
    assert [entry.seq for entry in await entries(database, org_id)] == [1]


async def test_a_refused_checkpoint_leaves_no_head_behind(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    async with database.org_session(org_id) as session:
        with pytest.raises(EmptyLedger):
            await checkpoint(session, Ed25519PrivateKey.generate())
        heads = (await session.execute(select(LedgerHead))).all()
    assert heads == []
    await write(database, org_id)
    stored = await entries(database, org_id)
    assert [entry.seq for entry in stored] == [1]
    async with database.org_session(org_id) as session:
        assert (await verify_ledger(session)).ok


def tamper(database: Database, column: str, expression: str, *values: object, seq: int = 2) -> None:
    """What only the database owner can do: the triggers go, then a cell is set to anything."""
    path = database.engine.url.database
    assert path is not None
    connection = sqlite3.connect(path)
    connection.execute("DROP TRIGGER IF EXISTS ledger_entries_no_update")
    connection.execute(f"UPDATE ledger_entries SET {column} = {expression} WHERE seq = {seq}")
    connection.commit()
    connection.close()


HOSTILE_CELLS = [
    ("refs", "'[1,2,3]'"),
    ("refs", "'123'"),
    ("refs", "'null'"),
    ("refs", "'\"text\"'"),
    ("refs", "'[]'"),
    ("refs", '\'[["n", "x"]]\''),
    ("refs", "'{\"n\": 5}'"),
    ("refs", "'{not json'"),
    ("seq", "'two'"),
    ("seq", "2.5"),
    ("at", "'yesterday'"),
    ("at", "7"),
    ("run_id", "'not a uuid'"),
    ("case_id", "'not a uuid'"),
    ("type", "7"),
    ("actor", "7"),
    ("inputs_sha256", "7"),
    ("outputs_sha256", "X'ff'"),
    ("prev", "7"),
    ("hash", "7"),
    ("hash", "X'ff'"),
]


@pytest.mark.parametrize(("column", "expression"), HOSTILE_CELLS)
async def test_a_hostile_cell_is_reported_not_raised(
    orgs: Orgs, column: str, expression: str
) -> None:
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    tamper(database, column, expression)
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session)
    assert not result.ok and result.entries == 3


async def test_a_deeply_nested_refs_cell_is_reported_not_raised(orgs: Orgs) -> None:
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    path = database.engine.url.database
    assert path is not None
    connection = sqlite3.connect(path)
    connection.execute("DROP TRIGGER IF EXISTS ledger_entries_no_update")
    connection.execute(
        "UPDATE ledger_entries SET refs = ? WHERE seq = 2", ("[" * 100000 + "]" * 100000,)
    )
    connection.commit()
    connection.close()
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session)
    assert not result.ok and 2 in {problem.seq for problem in result.problems}


async def test_a_row_the_driver_cannot_decode_is_reported_with_where_checking_stopped(
    orgs: Orgs,
) -> None:
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    tamper(database, "actor", "CAST(X'ff' AS TEXT)")
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session)
    assert not result.ok
    # Rows arrive in batches, so the bad row spoils its batch: checking stops after entry 0.
    assert [(problem.seq, problem.kind) for problem in result.problems] == [(1, "unreadable")]


@pytest.mark.parametrize("seq", [1, 2])
async def test_an_undecodable_first_row_is_reported_not_raised(orgs: Orgs, seq: int) -> None:
    """SQLAlchemy fetches the first batch while opening the stream, so a bad row in it fails
    there, before any row has been handed over."""
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    tamper(database, "actor", "CAST(X'ff' AS TEXT)", seq=seq)
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session)
    assert not result.ok
    assert [(problem.seq, problem.kind) for problem in result.problems] == [(1, "unreadable")]


class _FailsAfterOneRow:
    """A row stream whose second fetch raises `error`, as a driver does when it decodes a
    JSON cell while fetching (PostgreSQL), before any column processing can tolerate it."""

    def __init__(self, rows: Any, error: Exception) -> None:
        self.rows, self.error, self.fetched = rows.__aiter__(), error, 0

    def __aiter__(self) -> "_FailsAfterOneRow":
        return self

    async def __anext__(self) -> Any:
        if self.fetched == 1:
            raise self.error
        self.fetched += 1
        return await self.rows.__anext__()


@pytest.mark.parametrize("error", [RecursionError(), ValueError("bad"), TypeError("bad")])
async def test_a_row_that_fails_to_decode_while_fetching_is_reported(
    orgs: Orgs, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    database, org_id, _ = orgs
    await write(database, org_id, 3)
    real_stream = AsyncSession.stream

    async def stream(self: AsyncSession, *args: Any, **kwargs: Any) -> Any:
        return _FailsAfterOneRow(await real_stream(self, *args, **kwargs), error)

    monkeypatch.setattr(AsyncSession, "stream", stream)
    async with database.org_session(org_id) as session:
        result = await verify_ledger(session)
    assert not result.ok
    assert [(problem.seq, problem.kind) for problem in result.problems] == [(2, "unreadable")]


async def test_a_database_without_the_tables_is_not_an_unreadable_entry(tmp_path: Path) -> None:
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'empty.db').as_posix()}")
    try:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(text("DROP TABLE ledger_entries"))
        async with database.org_session(uuid.uuid4()) as session:
            with pytest.raises(OperationalError, match="no such table"):
                await verify_ledger(session)
    finally:
        await database.dispose()
