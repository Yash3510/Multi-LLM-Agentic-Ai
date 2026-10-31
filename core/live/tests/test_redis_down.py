import logging
import socket
import uuid
from datetime import timedelta

import pytest

from fource.live import LiveUnavailable, RedisLive, open_live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
MINUTE = timedelta(minutes=1)
PASSWORD = "not-the-real-password"


@pytest.fixture
def down() -> RedisLive:
    """A Redis URL on a local port nothing listens on: connections are refused at once."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    return RedisLive(f"redis://:{PASSWORD}@127.0.0.1:{port}/0")


async def test_the_cache_misses_and_drops_writes_when_redis_is_down(
    down: RedisLive, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    await down.cache.set(ORG, "key", b"x", MINUTE)
    assert await down.cache.get(ORG, "key") is None
    await down.cache.delete(ORG, "key")
    assert "skipped" in caplog.text and PASSWORD not in caplog.text
    await down.close()


async def test_the_rate_limit_fails_closed_and_never_names_the_url(down: RedisLive) -> None:
    with pytest.raises(LiveUnavailable) as refused:
        await down.limits.hit(ORG, "signin:10.0.0.1", limit=3, window=MINUTE)
    assert PASSWORD not in refused.value.message and "://" not in refused.value.message
    assert not await down.ping()
    await down.close()


def test_a_url_that_is_not_redis_is_refused_without_repeating_it() -> None:
    with pytest.raises(ValueError) as refused:
        RedisLive(f"http://:{PASSWORD}@localhost:6379/0")
    assert PASSWORD not in str(refused.value)


def test_no_url_means_this_process_holds_it() -> None:
    assert open_live(None).backend == "memory"
    assert open_live("redis://localhost:6379/0").backend == "redis"
