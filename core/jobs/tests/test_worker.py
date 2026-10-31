import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.db import Database, org_of
from fource.jobs import Handler, HeldJob, Job, Recurring, Worker, enqueue, take

pytestmark = pytest.mark.anyio
Orgs = tuple[Database, uuid.UUID, uuid.UUID]


async def queue(
    database: Database, org_id: uuid.UUID, kind: str = "test.work", **options: Any
) -> uuid.UUID:
    async with database.org_session(org_id) as session:
        return await enqueue(session, kind, **options)


async def jobs(database: Database, org_id: uuid.UUID) -> list[Job]:
    async with database.org_session(org_id) as session:
        return list((await session.scalars(select(Job).order_by(Job.created_at, Job.id))).all())


class Recorder:
    """A handler that notes what it ran, and can be told to fail or to queue follow-up work."""

    def __init__(self, fail: Exception | None = None, follow_up: bool = False) -> None:
        self.ran: list[HeldJob] = []
        self.fail, self.follow_up = fail, follow_up

    async def __call__(self, session: AsyncSession, job: HeldJob) -> None:
        self.ran.append(job)
        if self.follow_up:  # a write of the handler's, in the job's own transaction
            await enqueue(session, "test.next", {"after": str(job.id)})
        if self.fail is not None:
            raise self.fail


async def test_run_once_runs_due_jobs_in_every_organisation(orgs: Orgs, clock: Any) -> None:
    database, first, second = orgs
    await queue(database, first, payload={"n": 1})
    await queue(database, second, payload={"n": 2})
    recorder = Recorder()
    assert await Worker(database, {"test.work": Handler(recorder)}).run_once() == 2
    assert sorted((job.org_id, job.payload["n"]) for job in recorder.ran) == sorted(
        [(first, 1), (second, 2)]
    )
    assert [job.state for job in await jobs(database, first)] == ["done"]


async def test_a_handlers_writes_commit_with_its_job(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    job_id = await queue(database, first)
    await Worker(database, {"test.work": Handler(Recorder(follow_up=True))}).run_once()
    stored = await jobs(database, first)
    assert [(job.kind, job.state) for job in stored] == [
        ("test.work", "done"),
        ("test.next", "queued"),
    ]
    assert stored[1].payload == {"after": str(job_id)}


async def test_a_handler_that_fails_rolls_back_and_is_retried(
    orgs: Orgs, clock: Any, caplog: pytest.LogCaptureFixture
) -> None:
    database, first, _ = orgs
    await queue(database, first, max_attempts=2)
    recorder = Recorder(fail=ValueError("a line quoted from a document"), follow_up=True)
    worker = Worker(database, {"test.work": Handler(recorder)})
    with caplog.at_level(logging.WARNING, logger="fource.jobs"):
        assert await worker.run_once() == 1
    assert "will be retried: ValueError" in caplog.text
    assert "a line quoted from a document" not in caplog.text
    [job] = await jobs(database, first)  # the follow-up rolled back with the attempt
    assert (job.state, job.attempts, job.last_error) == ("queued", 1, "ValueError")
    clock.advance(timedelta(seconds=30))
    assert await worker.run_once() == 1
    [job] = await jobs(database, first)
    assert (job.state, job.attempts, job.finished_at) == ("failed", 2, clock.current)


async def test_an_attempt_that_lost_its_lease_rolls_back(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first)

    async def outlived(session: AsyncSession, job: HeldJob) -> None:
        clock.advance(timedelta(minutes=6))  # past the lease: another worker takes the job
        async with database.org_session(first) as other:
            assert await take(other, ["test.work"], lease=timedelta(minutes=5)) is not None
        await enqueue(session, "test.next")  # this attempt's write must not survive

    await Worker(database, {"test.work": Handler(outlived)}).run_once()
    [job] = await jobs(database, first)
    assert (job.kind, job.state, job.attempts) == ("test.work", "running", 2)


async def test_a_failure_after_the_lease_was_lost_is_logged_as_lost(
    orgs: Orgs, clock: Any, caplog: pytest.LogCaptureFixture
) -> None:
    database, first, _ = orgs
    await queue(database, first)

    async def outlived_then_failed(session: AsyncSession, job: HeldJob) -> None:
        clock.advance(timedelta(minutes=6))
        async with database.org_session(first) as other:
            assert await take(other, ["test.work"], lease=timedelta(minutes=5)) is not None
        raise ValueError("a line quoted from a document")

    worker = Worker(database, {"test.work": Handler(outlived_then_failed)})
    with caplog.at_level(logging.WARNING, logger="fource.jobs"):
        assert await worker.run_once() == 1
    [job] = await jobs(database, first)  # the other worker's hold is untouched
    assert (job.state, job.attempts, job.last_error) == ("running", 2, None)
    assert "taken over" in caplog.text and "will be retried" not in caplog.text
    assert "a line quoted from a document" not in caplog.text


async def test_a_job_whose_last_attempt_never_finished_fails(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first, max_attempts=1)
    async with database.org_session(first) as session:  # a worker that then stopped
        assert await take(session, ["test.work"], lease=timedelta(minutes=5)) is not None
    clock.advance(timedelta(minutes=6))
    recorder = Recorder()
    await Worker(database, {"test.work": Handler(recorder)}).run_once()
    [job] = await jobs(database, first)
    assert recorder.ran == [] and job.state == "failed"
    assert job.last_error is not None and "did not finish" in job.last_error


async def test_jobs_without_a_handler_wait(orgs: Orgs, clock: Any) -> None:
    database, first, _ = orgs
    await queue(database, first, "other.work")
    assert await Worker(database, {"test.work": Handler(Recorder())}).run_once() == 0
    assert [job.state for job in await jobs(database, first)] == ["queued"]


async def test_a_worker_with_no_handlers_takes_nothing(orgs: Orgs, clock: Any) -> None:
    database, first, second = orgs
    await queue(database, first)
    await queue(database, second)
    assert await Worker(database, {}).run_once() == 0
    for org_id in (first, second):
        assert [job.state for job in await jobs(database, org_id)] == ["queued"]


async def test_a_recurring_job_runs_once_per_interval_in_each_organisation(
    orgs: Orgs, clock: Any
) -> None:
    database, first, second = orgs
    recorder = Recorder()
    hourly = Recurring("test.work", every=timedelta(hours=1))
    worker = Worker(database, {"test.work": Handler(recorder)}, recurring=[hourly])
    assert await worker.run_once() == 2  # due at once in both organisations
    assert await worker.run_once() == 0  # the next ones wait an hour
    clock.advance(timedelta(minutes=59))
    assert await worker.run_once() == 0
    clock.advance(timedelta(minutes=1))
    assert await worker.run_once() == 2
    assert await worker.run_once() == 0  # each pass first queues the next occurrence
    states = [job.state for job in await jobs(database, first)]
    assert states == ["done", "done", "queued"]  # never more than one waiting
    assert len(await jobs(database, second)) == 3


async def test_a_recurring_job_needs_a_handler(orgs: Orgs) -> None:
    database, _, _ = orgs
    with pytest.raises(ValueError, match="test.work"):
        Worker(database, {}, recurring=[Recurring("test.work", every=timedelta(hours=1))])


async def test_run_finds_new_work_and_stops_after_the_running_job(orgs: Orgs) -> None:
    database, first, _ = orgs
    started, release = asyncio.Event(), asyncio.Event()

    async def slow(session: AsyncSession, job: HeldJob) -> None:
        started.set()
        await release.wait()

    worker = Worker(database, {"test.work": Handler(slow)}, poll_seconds=0.05)
    running = asyncio.create_task(worker.run())
    await queue(database, first)
    await asyncio.wait_for(started.wait(), 5)
    worker.stop()
    await asyncio.sleep(0.2)
    assert not running.done()  # the running job finishes first
    release.set()
    await asyncio.wait_for(running, 5)
    assert [job.state for job in await jobs(database, first)] == ["done"]


async def test_a_wake_up_ends_the_wait_early(orgs: Orgs) -> None:
    database, first, _ = orgs
    recorder = Recorder()
    idle = asyncio.Event()

    class Watched(Worker):
        async def run_once(self) -> int:
            attempts = await super().run_once()
            idle.set()  # a pass found nothing; the worker goes on to wait
            return attempts

    worker = Watched(database, {"test.work": Handler(recorder)}, poll_seconds=60)
    running = asyncio.create_task(worker.run())
    await asyncio.wait_for(idle.wait(), 5)
    await queue(database, first)
    worker.wake()
    try:
        # Only wake() can get the job run inside this time: the poll is a minute.
        async with asyncio.timeout(10):
            while not recorder.ran:
                await asyncio.sleep(0.05)
    finally:
        worker.stop()
        await asyncio.wait_for(running, 5)
    assert len(recorder.ran) == 1


@pytest.mark.parametrize(
    ("handlers", "options", "mentions"),
    [
        ({"test.work": Handler(Recorder(), lease=timedelta(0))}, {}, "lease"),
        ({"test.work": Handler(Recorder(), lease=timedelta(seconds=-1))}, {}, "lease"),
        (
            {"test.work": Handler(Recorder())},
            {"recurring": [Recurring("test.work", every=timedelta(0))]},
            "every",
        ),
        (
            {"test.work": Handler(Recorder())},
            {"recurring": [Recurring("test.work", every=timedelta(hours=-1))]},
            "every",
        ),
        ({"test.work": Handler(Recorder())}, {"poll_seconds": 0}, "poll_seconds"),
        ({"test.work": Handler(Recorder())}, {"poll_seconds": -1.5}, "poll_seconds"),
    ],
)
async def test_settings_that_cannot_work_are_refused(
    orgs: Orgs, handlers: dict[str, Handler], options: dict[str, Any], mentions: str
) -> None:
    database, _, _ = orgs
    with pytest.raises(ValueError, match=mentions):
        Worker(database, handlers, **options)


async def test_one_organisations_failure_does_not_stop_the_others(
    orgs: Orgs, clock: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    database, first, second = orgs
    await queue(database, first)
    await queue(database, second)
    real_take = take

    async def take_or_break(session: AsyncSession, *args: Any, **options: Any) -> HeldJob | None:
        if org_of(session) == first:
            raise RuntimeError("a line quoted from a document")
        return await real_take(session, *args, **options)

    monkeypatch.setattr("fource.jobs.worker.take", take_or_break)
    recorder = Recorder()
    worker = Worker(database, {"test.work": Handler(recorder)})
    with caplog.at_level(logging.WARNING, logger="fource.jobs"):
        assert await worker.run_once() == 1
    assert [job.org_id for job in recorder.ran] == [second]
    assert [job.state for job in await jobs(database, first)] == ["queued"]
    assert f"a pass over organisation {first} failed: RuntimeError" in caplog.text
    assert "a line quoted from a document" not in caplog.text


async def test_a_broken_organisation_is_logged_once_per_pass(
    orgs: Orgs, clock: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    database, first, second = orgs
    for _ in range(3):
        await queue(database, second)
    real_take = take

    async def take_or_break(session: AsyncSession, *args: Any, **options: Any) -> HeldJob | None:
        if org_of(session) == first:
            raise RuntimeError("a line quoted from a document")
        return await real_take(session, *args, **options)

    monkeypatch.setattr("fource.jobs.worker.take", take_or_break)
    worker = Worker(database, {"test.work": Handler(Recorder())})
    with caplog.at_level(logging.WARNING, logger="fource.jobs"):
        assert await worker.run_once() == 3
    assert caplog.text.count(f"a pass over organisation {first} failed") == 1


async def test_a_failure_keeping_recurring_jobs_queued_does_not_stop_the_others(
    orgs: Orgs, clock: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    database, first, second = orgs
    real_enqueue = enqueue

    async def enqueue_or_break(session: AsyncSession, *args: Any, **options: Any) -> uuid.UUID:
        if org_of(session) == first:
            raise RuntimeError("a line quoted from a document")
        return await real_enqueue(session, *args, **options)

    monkeypatch.setattr("fource.jobs.worker.enqueue", enqueue_or_break)
    recorder = Recorder()
    hourly = Recurring("test.work", every=timedelta(hours=1))
    worker = Worker(database, {"test.work": Handler(recorder)}, recurring=[hourly])
    with caplog.at_level(logging.WARNING, logger="fource.jobs"):
        assert await worker.run_once() == 1
    assert [job.org_id for job in recorder.ran] == [second]
    assert f"a pass over organisation {first} failed: RuntimeError" in caplog.text
    assert "a line quoted from a document" not in caplog.text


async def test_cancellation_is_not_swallowed_by_an_organisations_pass(
    orgs: Orgs, clock: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, first, _ = orgs
    await queue(database, first)

    async def cancelled(session: AsyncSession, *args: Any, **options: Any) -> HeldJob | None:
        raise asyncio.CancelledError

    monkeypatch.setattr("fource.jobs.worker.take", cancelled)
    with pytest.raises(asyncio.CancelledError):
        await Worker(database, {"test.work": Handler(Recorder())}).run_once()


async def test_two_workers_after_downtime_run_a_recurring_job_once(
    orgs: Orgs, clock: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, first, second = orgs
    recorder = Recorder()
    hourly = Recurring("test.work", every=timedelta(hours=1))
    handlers = {"test.work": Handler(recorder)}
    worker_a = Worker(database, handlers, recurring=[hourly])
    worker_b = Worker(database, handlers, recurring=[hourly])
    assert await worker_a.run_once() == 2  # 10:00 in both organisations
    clock.advance(timedelta(hours=2))  # downtime longer than the interval
    real_enqueue = enqueue
    interleaved = False

    async def enqueue_after_the_other_worker(
        session: AsyncSession, *args: Any, **options: Any
    ) -> uuid.UUID:
        # Worker A has looked and found nothing pending; now worker B queues and runs the due one.
        nonlocal interleaved
        if not interleaved:
            interleaved = True
            assert await worker_b.run_once() == 2
        return await real_enqueue(session, *args, **options)

    monkeypatch.setattr("fource.jobs.worker.enqueue", enqueue_after_the_other_worker)
    await worker_a.run_once()
    assert interleaved
    # First: 10:00 and 12:00, not 12:00 twice. Second: A looked after B, so it queued 13:00.
    assert [job.state for job in await jobs(database, first)] == ["done", "done"]
    assert [job.state for job in await jobs(database, second)] == ["done", "done", "queued"]
    assert len(recorder.ran) == 4  # two organisations, two intervals
