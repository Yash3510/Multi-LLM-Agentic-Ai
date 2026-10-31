import logging
import socket
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import cast

import pytest

from fource.live import LiveUnavailable, RedisLive, open_live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
MINUTE = timedelta(minutes=1)
PASSWORD = "not-the-real-password"


@pytest.fixture
async def down() -> AsyncIterator[RedisLive]:
    """A Redis URL on a local port nothing listens on: connections are refused at once."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    store = RedisLive(f"redis://:{PASSWORD}@127.0.0.1:{port}/0")
    try:
        yield store
    finally:
        await store.close()


async def test_the_cache_misses_and_drops_writes_when_redis_is_down(
    down: RedisLive, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    await down.cache.set(ORG, "key", b"x", MINUTE)
    assert await down.cache.get(ORG, "key") is None
    await down.cache.delete(ORG, "key")
    assert "skipped" in caplog.text and PASSWORD not in caplog.text


async def test_the_rate_limit_fails_closed_and_never_names_the_url(down: RedisLive) -> None:
    with pytest.raises(LiveUnavailable) as refused:
        await down.limits.hit(ORG, "signin:10.0.0.1", limit=3, window=MINUTE)
    assert PASSWORD not in refused.value.message and "://" not in refused.value.message
    assert not await down.ping()


async def test_taking_a_lock_fails_closed(down: RedisLive) -> None:
    with pytest.raises(LiveUnavailable):
        await down.locks.acquire(ORG, "index", MINUTE)


def test_a_url_that_is_not_redis_is_refused_without_repeating_it() -> None:
    with pytest.raises(ValueError) as refused:
        RedisLive(f"http://:{PASSWORD}@localhost:6379/0")
    assert PASSWORD not in str(refused.value)


async def test_no_url_means_this_process_holds_it() -> None:
    assert open_live(None).backend == "memory"
    store = open_live("redis://127.0.0.1:1/0")  # nothing listens on port 1; never connected
    try:
        assert store.backend == "redis"
    finally:
        await store.close()


async def test_a_key_is_built_only_from_an_organisation_id(down: RedisLive) -> None:
    """A text standing in for the organisation could carry glob characters or a `:` and reach
    into another organisation's keys, so anything but a UUID is refused before Redis is asked."""
    stranger = cast("uuid.UUID", "x:*")
    with pytest.raises(ValueError):
        await down.cache.get(stranger, "key")
    with pytest.raises(ValueError):
        await down.cache.set(stranger, "key", b"x", MINUTE)
    with pytest.raises(ValueError):
        await down.cache.delete(stranger, "key")
    with pytest.raises(ValueError):
        await down.limits.hit(stranger, "key", limit=3, window=MINUTE)
