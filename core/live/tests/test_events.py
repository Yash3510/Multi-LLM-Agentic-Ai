import asyncio
import uuid

import pytest

from fource.live import Event, Live

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


@pytest.mark.parametrize("data", [{"bad": float("nan")}, {"bad": object()}])
async def test_data_must_be_json(live: Live, data: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        await live.events.publish(ORG, TOPIC, data)


@pytest.mark.parametrize("topic", ["", "Run.1", "has space", "x" * 201])
async def test_odd_topics_are_refused(live: Live, topic: str) -> None:
    with pytest.raises(ValueError):
        await live.events.publish(ORG, topic, {})
