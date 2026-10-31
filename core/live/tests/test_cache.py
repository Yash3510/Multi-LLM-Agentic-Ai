import asyncio
import uuid
from datetime import timedelta

import pytest

from fource.live import Live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
OTHER = uuid.UUID("0192f5a0-0000-7000-8000-000000000002")
MINUTE = timedelta(minutes=1)


async def test_a_value_is_kept_until_it_is_deleted(live: Live) -> None:
    assert await live.cache.get(ORG, "answer") is None
    await live.cache.set(ORG, "answer", b"42", MINUTE)
    assert await live.cache.get(ORG, "answer") == b"42"
    await live.cache.delete(ORG, "answer")
    assert await live.cache.get(ORG, "answer") is None


async def test_a_value_expires_after_its_time_to_live(live: Live) -> None:
    await live.cache.set(ORG, "brief", b"x", timedelta(milliseconds=50))
    await asyncio.sleep(0.2)
    assert await live.cache.get(ORG, "brief") is None


async def test_each_organisation_has_its_own_cache(live: Live) -> None:
    await live.cache.set(ORG, "shared-name", b"first", MINUTE)
    assert await live.cache.get(OTHER, "shared-name") is None


@pytest.mark.parametrize(
    "ttl", [timedelta(0), timedelta(microseconds=999), timedelta(hours=24, seconds=1)]
)
async def test_a_time_to_live_is_from_a_millisecond_to_a_day(live: Live, ttl: timedelta) -> None:
    with pytest.raises(ValueError):
        await live.cache.set(ORG, "key", b"x", ttl)


@pytest.mark.parametrize("key", ["", "has space", "x" * 201, "ünïcode"])
async def test_odd_keys_are_refused(live: Live, key: str) -> None:
    with pytest.raises(ValueError):
        await live.cache.get(ORG, key)


async def test_the_store_answers_a_ping(live: Live) -> None:
    assert await live.ping()
