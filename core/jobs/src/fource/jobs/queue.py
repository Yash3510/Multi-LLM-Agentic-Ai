"""Putting work on the queue and taking it off, inside organisation sessions (ADR-0040)."""

import json
import re
import uuid
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import new_id, now
from fource.db import org_of
from fource.jobs.models import UNFINISHED, UNFINISHED_SQL, Job, JobState

CHANNEL = "fource_jobs"
MAX_PAYLOAD_BYTES = 16 * 1024
_KIND = re.compile(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*")
_KEY = re.compile(r"[A-Za-z0-9_.:-]{1,200}")
_UNSYNCED = {"synchronize_session": False}


@dataclass(frozen=True)
class HeldJob:
    """A job a worker holds: what its handler needs, and `holder`, the token of this hold (a
    fresh one each time a job is taken), which finishing the job must present."""

    id: uuid.UUID
    org_id: uuid.UUID
    kind: str
    payload: Mapping[str, object]
    attempts: int
    max_attempts: int
    holder: uuid.UUID


def _checked_payload(payload: Mapping[str, object] | None) -> dict[str, object]:
    data = dict(payload or {})
    try:
        encoded = json.dumps(data, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError("a job's payload is a JSON object") from error
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise ValueError(f"a job's payload is at most {MAX_PAYLOAD_BYTES} bytes of JSON")
    return data


async def enqueue(
    session: AsyncSession,
    kind: str,
    payload: Mapping[str, object] | None = None,
    *,
    run_at: datetime | None = None,
    key: str | None = None,
    max_attempts: int = 5,
) -> uuid.UUID:
    """Queues a job of the session's organisation in the session's transaction: it is queued
    with the state that needs it, or not at all. With a `key`, a job of that key that is still
    queued or running is kept and its id returned, so the same work is never queued twice.

    A payload holds ids and small parameters (JSON, at most 16 KiB), never document content
    or secrets. On PostgreSQL the commit also wakes listening workers (NOTIFY)."""
    if len(kind) > 100 or not _KIND.fullmatch(kind):
        raise ValueError(
            f"a job kind is lower case and dotted, such as ledger.checkpoint: {kind!r}"
        )
    if key is not None and not _KEY.fullmatch(key):
        raise ValueError(f"a job key is 1 to 200 letters, digits or _.:- : {key!r}")
    if isinstance(max_attempts, bool) or max_attempts < 1:
        raise ValueError("max_attempts counts from 1")
    org_id = org_of(session)
    data = _checked_payload(payload)
    dialect = (await session.connection()).dialect.name
    insert = postgresql_insert if dialect == "postgresql" else sqlite_insert
    # The insert comes first, so on SQLite this transaction takes the write lock before it reads.
    for _ in range(3):
        job_id = new_id()
        statement = insert(Job).values(
            id=job_id,
            org_id=org_id,
            created_at=now(),
            kind=kind,
            key=key,
            payload=data,
            state=JobState.QUEUED.value,
            run_at=run_at or now(),
            attempts=0,
            max_attempts=max_attempts,
        )
        if key is not None:
            statement = statement.on_conflict_do_nothing(
                index_elements=["org_id", "key"], index_where=text(UNFINISHED_SQL)
            )
        if (await session.execute(statement.returning(Job.id))).first() is not None:
            break
        pending = await session.scalar(
            select(Job.id).where(Job.org_id == org_id, Job.key == key, Job.state.in_(UNFINISHED))
        )
        if pending is not None:
            return pending
    else:  # the pending job finished between the insert and the look, three times over
        raise RuntimeError(f"the pending job with key {key!r} kept changing")
    if dialect == "postgresql":
        await session.execute(
            text("SELECT pg_notify(:channel, :org)"), {"channel": CHANNEL, "org": str(org_id)}
        )
    return job_id


async def take(
    session: AsyncSession, kinds: Collection[str], *, lease: timedelta
) -> HeldJob | None:
    """Takes the organisation's next due job of one of `kinds`, or a running one whose lease
    has run out, and holds it for `lease`. The caller commits at once.

    Call it as the transaction's first statement. On PostgreSQL the job's row is locked and
    other takers skip it (FOR UPDATE SKIP LOCKED). SQLite has no row locks and drops that
    clause, but the statement writes, so it takes the database's write lock before reading and
    takers queue: correct, one at a time (ADR-0010 point 5)."""
    org_id = org_of(session)
    current = now()
    token = new_id()
    due = (
        select(Job.id)
        .where(
            Job.org_id == org_id,
            Job.kind.in_(list(kinds)),
            or_(
                and_(Job.state == JobState.QUEUED.value, Job.run_at <= current),
                and_(Job.state == JobState.RUNNING.value, Job.locked_until < current),
            ),
        )
        .order_by(Job.run_at, Job.id)
        .limit(1)
        .with_for_update(skip_locked=True)
        .scalar_subquery()
    )
    taken = await session.execute(
        update(Job)
        .where(Job.id == due)
        .values(
            state=JobState.RUNNING.value,
            attempts=Job.attempts + 1,
            locked_until=current + lease,
            holder=token,
        )
        .returning(Job.id, Job.kind, Job.payload, Job.attempts, Job.max_attempts),
        execution_options=_UNSYNCED,
    )
    row = taken.first()
    if row is None:
        return None
    job_id, kind, payload, attempts, max_attempts = row
    return HeldJob(
        id=job_id,
        org_id=org_id,
        kind=kind,
        payload=payload,
        attempts=attempts,
        max_attempts=max_attempts,
        holder=token,
    )
