"""The worker loop: take a due job, run its handler, finish it, repeat (ADR-0040)."""

import asyncio
import logging
import math
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import now
from fource.db import Database, Org
from fource.jobs.errors import LeaseLost, Unfinished
from fource.jobs.models import UNFINISHED, Job
from fource.jobs.queue import HeldJob, complete, describe, enqueue, retry_or_fail, take
from fource.jobs.wakeups import listen_for_jobs

_log = logging.getLogger("fource.jobs")
_UNFINISHED = "The last attempt did not finish: its worker stopped or it outlived its lease."


@dataclass(frozen=True)
class Handler:
    """Runs one kind of job. `run` gets the job's organisation session, in which its writes
    commit together with the job's completion; it raises to fail the attempt. `lease` must be
    longer than the longest run: past it, another worker may start the job again (and only one
    of the two can commit)."""

    run: Callable[[AsyncSession, HeldJob], Awaitable[None]]
    lease: timedelta = timedelta(minutes=5)


@dataclass(frozen=True)
class Recurring:
    """A job the worker keeps queued in every organisation, once per `every`."""

    kind: str
    every: timedelta


class Worker:
    """Runs the jobs of the kinds it has handlers for, in every organisation in turn."""

    def __init__(
        self,
        database: Database,
        handlers: Mapping[str, Handler],
        *,
        recurring: Sequence[Recurring] = (),
        poll_seconds: float = 2.0,
    ) -> None:
        missing = [each.kind for each in recurring if each.kind not in handlers]
        if missing:
            raise ValueError(f"recurring jobs without a handler: {', '.join(missing)}")
        if any(each.lease <= timedelta(0) for each in handlers.values()):
            raise ValueError("a handler's lease lasts longer than zero")
        if any(each.every <= timedelta(0) for each in recurring):
            raise ValueError("a recurring job's interval (every) lasts longer than zero")
        if not (poll_seconds > 0) or not math.isfinite(poll_seconds):  # NaN fails both
            raise ValueError("poll_seconds is a positive, finite number")
        self._database = database
        self._handlers = dict(handlers)
        self._recurring = tuple(recurring)
        self._poll = poll_seconds
        # One lease for every job it takes: the longest any handler needs.
        self._lease = max((each.lease for each in handlers.values()), default=timedelta(minutes=5))
        self._stopping = asyncio.Event()
        self._woken = asyncio.Event()

    def stop(self) -> None:
        """Stop taking; the job that is running finishes first."""
        self._stopping.set()

    def wake(self) -> None:
        """Look for work now rather than at the next poll."""
        self._woken.set()

    async def run_once(self) -> int:
        """Keeps the recurring jobs queued, then runs due jobs until a pass over every
        organisation finds none, or stop() is called. Returns how many attempts it made. With
        no handlers there is nothing to take (and nothing recurring: those need a handler)."""
        if not self._handlers:
            return 0
        organisations = await self._organisations()
        failed: set[uuid.UUID] = set()  # skipped for the rest of the pass, logged once
        for org_id in organisations:
            await self._guarded(org_id, self._keep_all_queued(org_id), failed)
        attempts = 0
        while not self._stopping.is_set():
            ran = 0
            for org_id in organisations:
                if self._stopping.is_set():
                    break
                if org_id not in failed:
                    ran += await self._guarded(org_id, self._run_one(org_id), failed)
            if not ran:
                break
            attempts += ran
        return attempts

    async def run(self) -> None:
        """Runs jobs until stop(): a pass over every organisation, then a wait for a NOTIFY (on
        PostgreSQL) or the poll interval. A failed pass, such as a lost database, is logged and
        tried again at the next poll."""
        listener = None
        if self._database.engine.dialect.name == "postgresql":
            url = self._database.engine.url.render_as_string(hide_password=False)
            listener = asyncio.create_task(listen_for_jobs(url, self.wake, self._stopping))
        try:
            while not self._stopping.is_set():
                self._woken.clear()
                try:
                    await self.run_once()
                except Exception as error:  # the next poll tries again
                    _log.warning("a pass over the job queue failed: %s", describe(error))
                await self._wait()
        finally:
            if listener is not None:
                listener.cancel()
                await asyncio.gather(listener, return_exceptions=True)

    async def _wait(self) -> None:
        waits = [asyncio.ensure_future(event.wait()) for event in (self._woken, self._stopping)]
        try:
            await asyncio.wait(waits, timeout=self._poll, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for each in waits:
                each.cancel()

    async def _organisations(self) -> list[uuid.UUID]:
        async with self._database.session() as session:
            return list((await session.scalars(select(Org.id).order_by(Org.slug))).all())

    async def _guarded(
        self, org_id: uuid.UUID, step: Awaitable[int | None], failed: set[uuid.UUID]
    ) -> int:
        """Runs one organisation's step. If it fails, logs it, notes the organisation in `failed`
        and returns 0 so the pass goes on with the next organisation: one organisation's trouble
        never starves the others, nor floods the log. Cancellation is not an Exception and still
        propagates."""
        try:
            return await step or 0
        except Exception as error:
            failed.add(org_id)
            _log.warning("a pass over organisation %s failed: %s", org_id, describe(error))
            return 0

    async def _keep_all_queued(self, org_id: uuid.UUID) -> None:
        for each in self._recurring:
            await self._keep_queued(org_id, each)

    async def _keep_queued(self, org_id: uuid.UUID, recurring: Recurring) -> None:
        """Queues the next occurrence unless one is pending: due one interval after the last one
        finished, or now. The first look is its own transaction, so SQLite never upgrades a read
        lock. The insert comes first in the next one, and only after it (when this transaction
        holds the write lock, or the key's index entry) is the key looked at again: if another
        worker has finished an occurrence since the first look, that interval is taken and this
        transaction rolls back. An occurrence another worker has queued and not finished is
        caught by the key's partial unique index."""
        key = f"recurring:{recurring.kind}"
        mine = (Job.org_id == org_id, Job.key == key)
        async with self._database.org_session(org_id) as session:
            pending = await session.scalar(select(Job.id).where(*mine, Job.state.in_(UNFINISHED)))
            last = await session.scalar(select(func.max(Job.finished_at)).where(*mine))
        if pending is not None:
            return
        due = now() if last is None else max(now(), last + recurring.every)
        async with self._database.org_session(org_id) as session:
            await enqueue(session, recurring.kind, run_at=due, key=key)
            latest = await session.scalar(select(func.max(Job.finished_at)).where(*mine))
            if latest != last:
                await session.rollback()  # another worker ran this interval's occurrence

    async def _run_one(self, org_id: uuid.UUID) -> int:
        async with self._database.org_session(org_id) as session:
            job = await take(session, list(self._handlers), lease=self._lease)
        if job is None:
            return 0
        if job.attempts > job.max_attempts:  # the last attempt never finished
            await self._record_failure(org_id, job, Unfinished(_UNFINISHED))
            return 1
        try:
            async with self._database.org_session(org_id) as session:
                await self._handlers[job.kind].run(session, job)
                await complete(session, job)
        except LeaseLost:
            self._log_taken_over(job)
        except Exception as error:  # recorded on the job, never lost
            await self._record_failure(org_id, job, error)
        return 1

    async def _record_failure(self, org_id: uuid.UUID, job: HeldJob, error: BaseException) -> None:
        try:
            async with self._database.org_session(org_id) as session:
                again = await retry_or_fail(session, job, error)
        except LeaseLost:  # another worker holds the job: it records its own outcome
            self._log_taken_over(job)
            return
        outcome = "will be retried" if again else "failed for good"
        _log.warning("job %s (%s) %s: %s", job.id, job.kind, outcome, describe(error))

    @staticmethod
    def _log_taken_over(job: HeldJob) -> None:
        _log.warning("job %s was taken over by another worker; this attempt rolled back", job.id)
