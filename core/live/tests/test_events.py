import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from typing import Protocol, cast

import pytest
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.connection import parse_url

from fource.live import Event, Live, LiveUnavailable, MemoryLive, RedisLive

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
OTHER = uuid.UUID("0192f5a0-0000-7000-8000-000000000002")
TOPIC = "run.0192f5a0-0000-7000-8000-0000000000aa"


async def test_a_subscriber_gets_what_is_published_after_it_subscribed(live: Live) -> None:
    async with live.events.subscribe(ORG, TOPIC) as subscription:
        assert await live.events.publish(ORG, TOPIC, {"stage": "read", "seq": 3})
        event = await subscription.next(timeout=2)
    assert event == Event(topic=TOPIC, data={"stage": "read", "seq": 3})


async def test_events_stay_within_their_organisation_and_topic(live: Live) -> None:
    async with live.events.subscribe(ORG, TOPIC) as subscription:
        await live.events.publish(OTHER, TOPIC, {"to": "other"})
        await live.events.publish(ORG, "run.another", {"to": "another"})
        assert await subscription.next(timeout=0.3) is None


async def test_every_subscriber_gets_each_event_in_order(live: Live) -> None:
    async with (
        live.events.subscribe(ORG, TOPIC) as first,
        live.events.subscribe(ORG, TOPIC) as second,
    ):
        for seq in range(3):
            await live.events.publish(ORG, TOPIC, {"seq": seq})
        for subscription in (first, second):
            got = [await subscription.next(timeout=2) for _ in range(3)]
            assert [event.data["seq"] if event else None for event in got] == [0, 1, 2]


async def test_publishing_with_nobody_listening_is_fine(live: Live) -> None:
    assert await live.events.publish(ORG, TOPIC, {"seq": 1})


async def test_waiting_with_nothing_published_ends_with_none(live: Live) -> None:
    async with live.events.subscribe(ORG, TOPIC) as subscription:
        started = asyncio.get_running_loop().time()
        assert await subscription.next(timeout=0.2) is None
        assert asyncio.get_running_loop().time() - started >= 0.15


async def test_a_zero_timeout_still_returns_an_event_that_is_already_there(live: Live) -> None:
    async with live.events.subscribe(ORG, TOPIC) as subscription:
        await live.events.publish(ORG, TOPIC, {"seq": 1})
        await asyncio.sleep(0.3)  # time for Redis to deliver it; memory has it at once
        assert await subscription.next(timeout=0) == Event(topic=TOPIC, data={"seq": 1})


@pytest.mark.parametrize("data", [{"bad": float("nan")}, {"bad": object()}])
async def test_data_must_be_json(live: Live, data: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        await live.events.publish(ORG, TOPIC, data)


@pytest.mark.parametrize("topic", ["", "Run.1", "has space", "x" * 201])
async def test_odd_topics_are_refused(live: Live, topic: str) -> None:
    with pytest.raises(ValueError):
        await live.events.publish(ORG, topic, {})
    with pytest.raises(ValueError):
        async with live.events.subscribe(ORG, topic):
            pass


async def test_an_organisation_must_be_a_uuid(live: Live) -> None:
    stranger = cast("uuid.UUID", "x:*")
    with pytest.raises(ValueError):
        await live.events.publish(stranger, TOPIC, {})
    with pytest.raises(ValueError):
        async with live.events.subscribe(stranger, TOPIC):
            pass


async def test_a_subscriber_that_fell_behind_learns_it_missed_events() -> None:
    """Past 1000 unread events the memory backend cuts the subscriber off, as Redis does, so
    it reads the state again instead of trusting a stream with holes in it. After that the same
    subscription follows new events, as a reconnected Redis subscription does, and the old
    buffered ones are gone."""
    live = MemoryLive()
    async with live.events.subscribe(ORG, TOPIC) as subscription:
        for seq in range(1001):
            await live.events.publish(ORG, TOPIC, {"seq": seq})
        with pytest.raises(LiveUnavailable):
            await subscription.next(timeout=0.1)
        assert await subscription.next(timeout=0.1) is None
        await live.events.publish(ORG, TOPIC, {"seq": 2000})
        event = await subscription.next(timeout=1)
        assert event is not None
        assert event.data == {"seq": 2000}


class _Publisher(Protocol):
    """Redis.publish, whose redis-py signature leaves `**kwargs` untyped."""

    async def publish(self, channel: str, message: str) -> int: ...


@pytest.fixture
async def raw() -> AsyncIterator[tuple[RedisLive, _Publisher, str]]:
    """A store and a plain client on the same Redis, and the channel the store listens on."""
    url = os.environ.get("FOURCE_TEST_REDIS_URL")
    if not url:
        pytest.fail("Redis tests need FOURCE_TEST_REDIS_URL (see core/live/README.md)")
    prefix = f"fource_test_{uuid.uuid4().hex[:12]}"
    pool = ConnectionPool(**parse_url(url))
    client = Redis(connection_pool=pool)
    store = RedisLive(url, prefix=prefix)
    try:
        yield store, cast("_Publisher", client), f"{prefix}:{ORG}:events:{TOPIC}"
    finally:
        await client.aclose()
        await pool.aclose()
        await store.close()


@pytest.mark.redis
async def test_a_message_that_is_not_an_event_is_skipped(
    raw: tuple[RedisLive, _Publisher, str],
) -> None:
    store, client, channel = raw
    async with store.events.subscribe(ORG, TOPIC) as subscription:
        await client.publish(channel, "[1,2]")
        await store.events.publish(ORG, TOPIC, {"seq": 7})
        event = await subscription.next(timeout=2)
    assert event == Event(topic=TOPIC, data={"seq": 7})


@pytest.mark.redis
async def test_waiting_goes_on_after_a_message_that_is_not_an_event(
    raw: tuple[RedisLive, _Publisher, str],
) -> None:
    store, client, channel = raw
    async with store.events.subscribe(ORG, TOPIC) as subscription:
        await client.publish(channel, "[1,2]")
        started = asyncio.get_running_loop().time()
        assert await subscription.next(timeout=1) is None
        assert asyncio.get_running_loop().time() - started >= 0.9
