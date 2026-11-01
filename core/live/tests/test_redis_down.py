import logging
import socket
import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import cast

import pytest
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from fource.live import LiveUnavailable, RedisLive, RedisLock, open_live

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0192f5a0-0000-7000-8000-000000000001")
MINUTE = timedelta(minutes=1)
PASSWORD = "not-the-real-password"


def _refused_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class _Pipe:
    """A pipeline whose EXEC answers `results`, as a server that does not abort EXEC when a
    watched key has expired does for a command that found no key."""

    def __init__(self, token: bytes, results: list[object]) -> None:
        self._token, self._results = token, results

    async def __aenter__(self) -> "_Pipe":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def watch(self, *_: object) -> bool:
        return True

    async def get(self, _: object) -> bytes:
        return self._token

    def multi(self) -> None:
        return None

    def pexpire(self, *_: object) -> None:
        return None

    def delete(self, *_: object) -> None:
        return None

    async def execute(self) -> list[object]:
        return self._results


class _Client:
    def __init__(self, pipe: _Pipe) -> None:
        self._pipe = pipe

    def pipeline(self, transaction: bool = True) -> _Pipe:
        return self._pipe


@pytest.fixture
async def down() -> AsyncIterator[RedisLive]:
    """A Redis URL on a local port nothing listens on: connections are refused at once."""
    port = _refused_port()
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


async def test_publishing_says_it_was_not_sent_and_subscribing_fails(
    down: RedisLive, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING)
    assert not await down.events.publish(ORG, "run.1", {"seq": 1})
    with pytest.raises(LiveUnavailable):
        async with down.events.subscribe(ORG, "run.1"):
            pass
    assert PASSWORD not in caplog.text


@pytest.mark.parametrize("outcome, expected", [(0, False), (1, True)])
async def test_a_lock_changes_only_when_the_command_found_its_key(
    outcome: int, expected: bool
) -> None:
    """EXEC answering 0 for PEXPIRE or DEL means the key was gone: not ours any more."""
    pipe = _Pipe(b"token", [outcome])
    lock = RedisLock(cast("Redis", _Client(pipe)), "fource:lock", "token")
    assert await lock.extend(MINUTE) is expected
    assert await lock.release() is expected


async def test_a_lock_on_a_down_redis_cannot_be_extended_and_release_is_false(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    client = Redis(  # built as the store builds its own: no retries, a short connect timeout
        host="127.0.0.1",
        port=_refused_port(),
        password=PASSWORD,
        retry=Retry(NoBackoff(), 0),
        socket_connect_timeout=2.0,
    )
    try:
        lock = RedisLock(client, "fource:lock", "token")
        with pytest.raises(LiveUnavailable) as refused:
            await lock.extend(MINUTE)
        assert PASSWORD not in refused.value.message and "://" not in refused.value.message
        assert not await lock.release()
    finally:
        await client.aclose()
    assert "skipped" in caplog.text and PASSWORD not in caplog.text
    assert "127.0.0.1" not in caplog.text


def test_a_url_that_is_not_redis_is_refused_without_repeating_it() -> None:
    with pytest.raises(ValueError) as refused:
        RedisLive(f"http://:{PASSWORD}@localhost:6379/0")
    assert PASSWORD not in str(refused.value)


@pytest.mark.parametrize(
    "option", ["socket_timeout", "socket_connect_timeout", "health_check_interval", "retry"]
)
def test_a_url_cannot_change_what_the_pool_sets_itself(option: str) -> None:
    with pytest.raises(ValueError) as refused:
        RedisLive(f"redis://:{PASSWORD}@127.0.0.1:1/0?{option}=5")
    assert PASSWORD not in str(refused.value) and "://" not in str(refused.value)


@pytest.mark.parametrize("query", ["decode_responses=true", "bogus=1", "host=elsewhere", "DB=1"])
def test_a_url_may_set_only_the_options_that_are_allowed(query: str) -> None:
    with pytest.raises(ValueError) as refused:
        RedisLive(f"redis://:{PASSWORD}@127.0.0.1:1/0?{query}")
    assert PASSWORD not in str(refused.value) and "://" not in str(refused.value)


@pytest.mark.parametrize(
    "url",
    [
        f"redis://:{PASSWORD}@127.0.0.1:1/0?ssl_cert_reqs=required",
        f"redis://:{PASSWORD}@127.0.0.1:1/0?db=1&ssl_check_hostname=true",
        f"unix://:{PASSWORD}@/tmp/redis.sock?ssl_ca_certs=/tmp/ca.pem",
    ],
)
def test_trust_settings_need_a_rediss_url(url: str) -> None:
    """On redis:// or unix:// they would only fail at the first connection, as a TypeError."""
    with pytest.raises(ValueError) as refused:
        RedisLive(url)
    assert PASSWORD not in str(refused.value) and "://" not in str(refused.value)


async def test_a_unix_url_may_choose_its_database() -> None:
    store = RedisLive("unix:///tmp/redis.sock?db=2")
    await store.close()


async def test_a_url_may_choose_its_database_and_trust_settings() -> None:
    store = RedisLive("rediss://127.0.0.1:1/0?db=2&ssl_cert_reqs=required&ssl_check_hostname=true")
    await store.close()


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
