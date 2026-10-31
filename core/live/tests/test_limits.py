import asyncio
import uuid
from datetime import timedelta

import pytest

from fource.live import Live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
OTHER = uuid.UUID("0192f5a0-0000-7000-8000-000000000002")
MINUTE = timedelta(minutes=1)


async def test_hits_are_allowed_up_to_the_limit_then_refused(live: Live) -> None:
    hits = [await live.limits.hit(ORG, "signin:10.0.0.1", limit=3, window=MINUTE) for _ in range(5)]
    assert [hit.count for hit in hits] == [1, 2, 3, 4, 5]
    assert [hit.allowed for hit in hits] == [True, True, True, False, False]
    assert timedelta(seconds=50) < hits[-1].retry_after <= MINUTE


async def test_keys_and_organisations_count_apart(live: Live) -> None:
    for _ in range(3):
        await live.limits.hit(ORG, "signin:10.0.0.1", limit=3, window=MINUTE)
    assert (await live.limits.hit(ORG, "signin:10.0.0.2", limit=3, window=MINUTE)).allowed
    assert (await live.limits.hit(OTHER, "signin:10.0.0.1", limit=3, window=MINUTE)).allowed


async def test_the_count_starts_again_after_the_window(live: Live) -> None:
    window = timedelta(milliseconds=200)
    for _ in range(2):
        await live.limits.hit(ORG, "burst", limit=1, window=window)
    await asyncio.sleep(0.4)
    hit = await live.limits.hit(ORG, "burst", limit=1, window=window)
    assert (hit.allowed, hit.count) == (True, 1)


async def test_hits_sent_together_are_each_counted(live: Live) -> None:
    hits = await asyncio.gather(
        *(live.limits.hit(ORG, "flood", limit=5, window=MINUTE) for _ in range(20))
    )
    assert sorted(hit.count for hit in hits) == list(range(1, 21))
    assert sum(hit.allowed for hit in hits) == 5


@pytest.mark.parametrize("limit", [0, -1, True])
async def test_a_limit_counts_from_one(live: Live, limit: int) -> None:
    with pytest.raises(ValueError):
        await live.limits.hit(ORG, "key", limit=limit, window=MINUTE)


@pytest.mark.parametrize("window", [timedelta(0), timedelta(hours=24, seconds=1)])
async def test_a_window_is_from_a_millisecond_to_a_day(live: Live, window: timedelta) -> None:
    with pytest.raises(ValueError):
        await live.limits.hit(ORG, "key", limit=1, window=window)
