import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from fource.db import Database
from fource.jobs import Job, JobState

pytestmark = pytest.mark.anyio
Orgs = tuple[Database, uuid.UUID, uuid.UUID]
AT = datetime(2026, 11, 14, 10, 0, tzinfo=UTC)


def job(state: str, key: str | None = "document:d-1") -> Job:
    return Job(
        kind="test.work", key=key, payload={}, state=state, run_at=AT, attempts=0, max_attempts=5
    )


async def test_the_table_keeps_one_unfinished_job_per_key(orgs: Orgs) -> None:
    database, first, second = orgs
    async with database.org_session(first) as session:  # finished ones may repeat a key
        session.add_all([job("done"), job("failed"), job("queued"), job("queued", key=None)])
    for state in (JobState.QUEUED, JobState.RUNNING):
        with pytest.raises(IntegrityError):
            async with database.org_session(first) as session:
                session.add(job(state))
    async with database.org_session(second) as session:  # each organisation has its own keys
        session.add(job("queued"))


async def test_a_job_is_in_one_of_four_states(orgs: Orgs) -> None:
    database, first, _ = orgs
    with pytest.raises(IntegrityError):
        async with database.org_session(first) as session:
            session.add(job("lost", key=None))
