import asyncio
import uuid
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select

from fource.common import FourceError
from fource.db import Database
from fource.jobs import (
    MAX_PAYLOAD_BYTES,
    HeldJob,
    Job,
    LeaseLost,
    backoff,
    complete,
    describe,
    enqueue,
    retry_or_fail,
    take,
)

pytestmark = pytest.mark.anyio
LEASE = timedelta(minutes=5)
Orgs = tuple[Database, uuid.UUID, uuid.UUID]


async def queue(
    database: Database, org_id: uuid.UUID, kind: str = "test.work", **options: Any
) -> uuid.UUID:
    async with database.org_session(org_id) as session:
        return await enqueue(session, kind, **options)


async def next_job(
    database: Database, org_id: uuid.UUID, kinds: tuple[str, ...] = ("test.work",)
) -> HeldJob | None:
    async with database.org_session(org_id) as session:
        return await take(session, kinds, lease=LEASE)


async def stored(database: Database, org_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    async with database.org_session(org_id) as session:
        return (await session.scalars(select(Job).where(Job.id == job_id))).one()


async def test_a_queued_job_is_taken_in_its_own_organisation_only(orgs: Orgs, clock: Any) -> None:
    database, first, second = orgs
    job_id = await queue(database, first, payload={"document": "d-1"})
    assert await next_job(database, second) is None
    job = await next_job(database, first)
    assert job is not None and (job.id, job.org_id, job.kind) == (job_id, first, "test.work")
    assert (job.payload, job.attempts, job.max_attempts) == ({"document": "d-1"}, 1, 5)
    row = await stored(database, first, job_id)
    assert (row.state, row.holder, row.locked_until) == (
        "running",
        job.holder,
        clock.current + LEASE,
    )


@pytest.mark.parametrize(
    "options",
    [
        {"kind": ""},
        {"kind": "Test.Work"},
        {"kind": "test work"},
        {"kind": "x" * 101},
        {"key": ""},
        {"key": "has space"},
        {"key": "x" * 201},
        {"payload": {"x": float("nan")}},
        {"payload": {"x": object()}},
        {"payload": {"big": "x" * MAX_PAYLOAD_BYTES}},
        {"max_attempts": 0},
        {"max_attempts": True},
    ],
)
async def test_malformed_jobs_are_refused(orgs: Orgs, options: dict[str, Any]) -> None:
    database, first, _ = orgs
    kind = options.pop("kind", "test.work")
    with pytest.raises(ValueError):
        await queue(database, first, kind, **options)


async def test_a_key_keeps_one_unfinished_job(orgs: Orgs, clock: Any) -> None:
    database, first, second = orgs
    once = await queue(database, first, key="document:d-1")
    assert await queue(database, first, key="document:d-1") == once
    assert await queue(database, second, key="document:d-1") != once  # each organisation its own
    job = await next_job(database, first)
    assert job is not None and job.id == once
    assert await queue(database, first, key="document:d-1") == once  # still running


async def test_a_job_waits_for_its_time(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first, run_at=clock.current + timedelta(minutes=10))
    assert await next_job(database, first) is None
    clock.advance(timedelta(minutes=10))
    assert await next_job(database, first) is not None


async def test_the_oldest_due_job_is_taken_first(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    later = await queue(database, first, run_at=clock.current - timedelta(minutes=1))
    earliest = await queue(database, first, run_at=clock.current - timedelta(minutes=3))
    middle = await queue(database, first, run_at=clock.current - timedelta(minutes=2))
    taken = [await next_job(database, first) for _ in range(3)]
    assert [job.id if job else None for job in taken] == [earliest, middle, later]


async def test_only_the_kinds_asked_for_are_taken(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first, "other.work")
    assert await next_job(database, first) is None
    assert await next_job(database, first, ("other.work",)) is not None


async def test_a_taken_job_comes_back_only_after_its_lease(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first)
    held = await next_job(database, first)
    assert held is not None and await next_job(database, first) is None
    clock.advance(LEASE + timedelta(seconds=1))
    again = await next_job(database, first)
    assert again is not None and again.id == held.id
    assert again.attempts == 2 and again.holder != held.holder


async def test_takers_working_together_take_each_job_once(orgs: Orgs) -> None:
    database, first, _ = orgs
    expected = {await queue(database, first) for _ in range(20)}

    async def taker() -> list[uuid.UUID]:
        taken: list[uuid.UUID] = []
        while (job := await next_job(database, first)) is not None:
            taken.append(job.id)
        return taken

    results = await asyncio.gather(*(taker() for _ in range(5)))
    every = [job_id for taken in results for job_id in taken]
    assert len(every) == 20 and set(every) == expected


async def test_a_finished_jobs_key_can_be_queued_again(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    once = await queue(database, first, key="document:d-1")
    job = await next_job(database, first)
    assert job is not None
    async with database.org_session(first) as session:
        await complete(session, job)
    assert await queue(database, first, key="document:d-1") != once


async def test_only_the_current_holder_can_complete_a_job(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    job_id = await queue(database, first)
    stale = await next_job(database, first)
    clock.advance(LEASE + timedelta(seconds=1))
    current = await next_job(database, first)
    assert stale is not None and current is not None
    with pytest.raises(LeaseLost):
        async with database.org_session(first) as session:
            await complete(session, stale)
    async with database.org_session(first) as session:
        await complete(session, current)
    row = await stored(database, first, job_id)
    assert (row.state, row.finished_at, row.holder) == ("done", clock.current, None)


async def test_a_failed_attempt_waits_then_the_job_fails_for_good(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    job_id = await queue(database, first, max_attempts=2)
    job = await next_job(database, first)
    assert job is not None
    async with database.org_session(first) as session:
        assert await retry_or_fail(session, job, ValueError("text from a document"))
    row = await stored(database, first, job_id)
    assert (row.state, row.run_at, row.last_error) == (
        "queued",
        clock.current + timedelta(seconds=30),
        "ValueError",
    )
    assert await next_job(database, first) is None
    clock.advance(timedelta(seconds=30))
    job = await next_job(database, first)
    assert job is not None and job.attempts == 2
    async with database.org_session(first) as session:
        assert not await retry_or_fail(session, job, FourceError("The signing key is missing."))
    row = await stored(database, first, job_id)
    assert (row.state, row.finished_at, row.last_error) == (
        "failed",
        clock.current,
        "The signing key is missing.",
    )


def test_only_messages_written_for_people_are_kept() -> None:
    assert describe(FourceError("The signing key is missing.")) == "The signing key is missing."
    assert describe(ValueError("a line quoted from a document")) == "ValueError"
    assert len(describe(FourceError("x" * 5000))) == 1000


def test_retries_wait_longer_each_time_up_to_an_hour() -> None:
    waits = [backoff(attempts) for attempts in range(1, 10)]
    assert waits[:4] == [timedelta(seconds=s) for s in (30, 60, 120, 240)]
    assert waits[-1] == backoff(10**9) == timedelta(hours=1)
