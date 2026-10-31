import asyncio
import uuid
from datetime import timedelta

import pytest

from fource.live import Live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
OTHER = uuid.UUID("0192f5a0-0000-7000-8000-000000000002")
MINUTE = timedelta(minutes=1)


async def test_a_lock_has_one_holder_until_it_is_released(live: Live) -> None:
    first = await live.locks.acquire(ORG, "index", MINUTE)
    assert first is not None
    assert await live.locks.acquire(ORG, "index", MINUTE) is None
    assert await first.release()
    assert not await first.release()  # once only
    assert await live.locks.acquire(ORG, "index", MINUTE) is not None


async def test_each_organisation_has_its_own_locks(live: Live) -> None:
    assert await live.locks.acquire(ORG, "index", MINUTE) is not None
    assert await live.locks.acquire(OTHER, "index", MINUTE) is not None


async def test_an_expired_lock_is_free_and_its_old_holder_cannot_touch_it(live: Live) -> None:
    old = await live.locks.acquire(ORG, "index", timedelta(milliseconds=100))
    assert old is not None
    await asyncio.sleep(0.3)
    new = await live.locks.acquire(ORG, "index", MINUTE)
    assert new is not None
    assert not await old.extend(MINUTE)
    assert not await old.release()  # it can't release the new holder's lock
    assert await live.locks.acquire(ORG, "index", MINUTE) is None


async def test_extending_keeps_the_lock(live: Live) -> None:
    held = await live.locks.acquire(ORG, "index", timedelta(milliseconds=200))
    assert held is not None
    assert await held.extend(MINUTE)
    await asyncio.sleep(0.4)
    assert await live.locks.acquire(ORG, "index", MINUTE) is None


async def test_only_one_of_many_takers_gets_the_lock(live: Live) -> None:
    taken = await asyncio.gather(*(live.locks.acquire(ORG, "once", MINUTE) for _ in range(10)))
    assert sum(lock is not None for lock in taken) == 1
