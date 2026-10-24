"""Writing and reading the ledger in the database, inside an organisation session."""

import uuid
from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from typing import Any, cast

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from sqlalchemy import Dialect, select, type_coerce, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import TypeDecorator, TypeEngine

from fource.common import new_id, now
from fource.db import org_of
from fource.ledger.chain import (
    GENESIS,
    SYSTEM,
    Entry,
    EntryType,
    format_time,
    make_entry,
    to_millis,
)
from fource.ledger.checkpoints import Checkpoint, sign_checkpoint
from fource.ledger.errors import EmptyLedger, UnreadableEntry
from fource.ledger.models import LedgerEntry, LedgerHead
from fource.ledger.verify import ChainVerifier, Verification

_UNSYNCED = {"synchronize_session": False}


async def _reserve(session: AsyncSession, org_id: uuid.UUID) -> tuple[int, str]:
    """The next seq and the hash it links to. Both statements write, so the head row stays
    locked until the transaction ends: on PostgreSQL the row lock, on SQLite the write lock.
    Concurrent writers wait their turn instead of taking the same number."""
    connection = await session.connection()
    insert = postgresql_insert if connection.dialect.name == "postgresql" else sqlite_insert
    first = insert(LedgerHead).values(
        id=new_id(), org_id=org_id, created_at=now(), seq=0, hash=GENESIS
    )
    await session.execute(first.on_conflict_do_nothing(index_elements=["org_id"]))
    taken = await session.execute(
        update(LedgerHead)
        .where(LedgerHead.org_id == org_id)
        .values(seq=LedgerHead.seq + 1)
        .returning(LedgerHead.seq, LedgerHead.hash),
        execution_options=_UNSYNCED,
    )
    seq, prev = taken.one()
    return seq, prev


async def _write(
    session: AsyncSession,
    org_id: uuid.UUID,
    seq: int,
    prev: str,
    moment: datetime,
    entry_type: EntryType,
    *,
    actor: str,
    refs: Mapping[str, str],
    inputs_sha256: str | None,
    outputs_sha256: str | None,
    run_id: uuid.UUID | None,
    case_id: uuid.UUID | None,
) -> Entry:
    entry = make_entry(
        seq=seq,
        at=format_time(moment),
        org=str(org_id),
        run=None if run_id is None else str(run_id),
        case=None if case_id is None else str(case_id),
        type=entry_type.value,
        actor=actor,
        inputs_sha256=inputs_sha256,
        outputs_sha256=outputs_sha256,
        refs=refs,
        prev=prev,
    )
    session.add(
        LedgerEntry(
            org_id=org_id,
            created_at=moment,
            seq=seq,
            at=moment,
            run_id=run_id,
            case_id=case_id,
            type=entry.type,
            actor=entry.actor,
            inputs_sha256=inputs_sha256,
            outputs_sha256=outputs_sha256,
            refs=dict(entry.refs),
            prev=prev,
            hash=entry.hash,
        )
    )
    await session.flush()
    await session.execute(
        update(LedgerHead).where(LedgerHead.org_id == org_id).values(hash=entry.hash),
        execution_options=_UNSYNCED,
    )
    return entry


async def append(
    session: AsyncSession,
    entry_type: EntryType,
    *,
    actor: str,
    refs: Mapping[str, str] | None = None,
    inputs_sha256: str | None = None,
    outputs_sha256: str | None = None,
    run_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
) -> Entry:
    """Adds the next entry of the session's organisation, in the session's transaction: it
    is committed with the action it records, or not at all."""
    org_id = org_of(session)
    seq, prev = await _reserve(session, org_id)
    return await _write(
        session,
        org_id,
        seq,
        prev,
        to_millis(now()),
        entry_type,
        actor=actor,
        refs=refs or {},
        inputs_sha256=inputs_sha256,
        outputs_sha256=outputs_sha256,
        run_id=run_id,
        case_id=case_id,
    )


async def checkpoint(session: AsyncSession, private_key: Ed25519PrivateKey) -> Checkpoint:
    """Signs the chain head and records the signature as the next entry (type checkpoint).

    The returned checkpoint is the copy to keep outside the database (ADR-0014)."""
    org_id = org_of(session)
    # A ledger only goes from empty to not empty, so this unlocked look is safe, and it writes
    # nothing: a caller that catches EmptyLedger and commits must not leave a head behind.
    last = await session.scalar(select(LedgerHead.seq).where(LedgerHead.org_id == org_id))
    if not last:
        raise EmptyLedger("The ledger has no entries to checkpoint yet.")
    seq, prev = await _reserve(session, org_id)
    moment = to_millis(now())
    signed = sign_checkpoint(
        private_key, org=str(org_id), seq=seq - 1, hash=prev, at=format_time(moment)
    )
    refs = {"seq": str(signed.seq), "hash": prev, "key": signed.key, "signature": signed.signature}
    await _write(
        session,
        org_id,
        seq,
        prev,
        moment,
        EntryType.CHECKPOINT,
        actor=SYSTEM,
        refs=refs,
        inputs_sha256=None,
        outputs_sha256=None,
        run_id=None,
        case_id=None,
    )
    return signed


class _Tolerant(TypeDecorator[Any]):
    """Reads a cell as `inner` would, but hands back what is stored when that can't be done.

    SQLite keeps whatever it is given, so a tampered cell can be text where a number or a
    UUID belongs. The verifier must see that as an altered entry, not fail on it."""

    impl = TypeEngine
    cache_ok = True

    def __init__(self, inner: TypeEngine[Any]) -> None:
        super().__init__()
        self.inner = inner

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        return self.inner.dialect_impl(dialect)

    def result_processor(self, dialect: Dialect, coltype: object) -> Any:
        process = self.inner.dialect_impl(dialect).result_processor(dialect, coltype)
        if process is None:
            return None

        def read(value: object) -> object:
            try:
                return process(value)
            except Exception:  # an unparseable cell: what is stored is the answer
                return value

        return read


_COLUMNS = [
    type_coerce(column, _Tolerant(column.type)).label(column.name)
    for column in LedgerEntry.__table__.columns
    if column.name not in {"id", "org_id", "created_at"}
]
# The marker's name can't be a ref name (they start with a lower-case letter), so an entry
# whose refs weren't an object never hashes as one that was.
_NOT_AN_OBJECT = "!refs"


def _entry(row: Any, org: str) -> Entry:
    """An entry as stored. The cells are not trusted: they come back as they are, and it is the
    hash check that reports them."""
    refs: object = row.refs
    return Entry(
        seq=row.seq,
        at=format_time(row.at) if isinstance(row.at, datetime) else str(row.at),
        org=org,
        run=None if row.run_id is None else str(row.run_id),
        case=None if row.case_id is None else str(row.case_id),
        type=row.type,
        actor=row.actor,
        inputs_sha256=row.inputs_sha256,
        outputs_sha256=row.outputs_sha256,
        refs=dict(cast("dict[str, str]", refs))
        if isinstance(refs, dict)
        else {_NOT_AN_OBJECT: repr(refs)},
        prev=row.prev,
        hash=row.hash,
    )


async def read_entries(session: AsyncSession) -> AsyncIterator[Entry]:
    """The session's organisation's entries in seq order, streamed.

    Reads whatever the rows hold, so that verifying reports a tampered entry instead of failing
    on it. Raises UnreadableEntry if the database can't return a row at all."""
    org_id = org_of(session)
    rows = await session.stream(
        select(*_COLUMNS).where(LedgerEntry.org_id == org_id).order_by(LedgerEntry.seq)
    )
    last = 0
    while True:
        try:
            row = await anext(aiter(rows), None)
        except DBAPIError as error:
            raise UnreadableEntry(last + 1) from error
        if row is None:
            return
        seq: object = row.seq
        if isinstance(seq, int):
            last = seq
        yield _entry(row, str(org_id))


async def verify_ledger(
    session: AsyncSession,
    *,
    public_key: Ed25519PublicKey | None = None,
    checkpoints: list[Checkpoint] | None = None,
) -> Verification:
    verifier = ChainVerifier(
        str(org_of(session)), public_key=public_key, checkpoints=checkpoints or []
    )
    try:
        async for entry in read_entries(session):
            verifier.add(entry)
    except UnreadableEntry as error:
        verifier.unreadable(error.seq)
    return verifier.finish()
