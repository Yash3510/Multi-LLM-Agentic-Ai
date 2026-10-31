"""The Redis backend (ADR-0026). Every key and channel is `<prefix>:<org>:<kind>:<name>`.

When Redis can't be reached: the cache misses and drops writes, publishing returns False, and
the rate limiter, lock taking and subscribing raise LiveUnavailable (they fail closed). No
message carries the URL, which holds the password.
"""

import asyncio
import logging
import secrets
import uuid
from collections.abc import AsyncGenerator, Callable, Mapping
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Protocol, cast
from urllib.parse import parse_qs, urlparse

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import Pipeline, PubSub
from redis.asyncio.connection import parse_url
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError, WatchError

from fource.live.base import (
    Event,
    Hit,
    LiveUnavailable,
    check_limit,
    check_name,
    check_topic,
    check_ttl,
    decode_event,
    encode_event,
)

_log = logging.getLogger("fource.live")
_DOWN = (RedisError, OSError)
_TIMEOUT = 2.0  # seconds to connect or to answer: a down Redis must not stall a sign-in
_NOT_A_URL = "FOURCE_REDIS_URL is not a redis://, rediss:// or unix:// URL"
# The only query options a URL may carry. Anything else is refused: the pool sets the timeouts
# and retries itself, and an option such as decode_responses would change what the client
# returns and break the byte values the cache hands back.
_QUERY_KEYS = (
    "db",
    "ssl_cert_reqs",
    "ssl_ca_certs",
    "ssl_certfile",
    "ssl_keyfile",
    "ssl_check_hostname",
)
_OPTIONS = "FOURCE_REDIS_URL may set only these query options: " + ", ".join(_QUERY_KEYS)


class _Untyped(Protocol):
    """The client calls whose redis-py signatures leave `**kwargs` untyped, as used here."""

    def pubsub(self) -> PubSub: ...

    async def publish(self, channel: str, message: str) -> int: ...

    async def ping(self) -> bool: ...


class _Messages(Protocol):
    """PubSub.get_message, whose redis-py signature returns an untyped dict."""

    async def get_message(
        self, ignore_subscribe_messages: bool = False, timeout: float | None = 0.0
    ) -> dict[str, object] | None: ...


def _unavailable() -> LiveUnavailable:
    return LiveUnavailable("The live store (Redis) can't be reached.")


class _Names:
    def __init__(self, prefix: str) -> None:
        self._prefix = prefix

    def __call__(self, org: object, kind: str, name: str) -> str:
        # Typed `object` so the check is real: a text could hold `:` or a glob, and the key
        # must be built from the UUID alone, never from whatever a caller passed.
        if not isinstance(org, uuid.UUID):
            raise ValueError("an organisation is identified by a UUID")
        return f"{self._prefix}:{org}:{kind}:{name}"


class RedisCache:
    def __init__(self, client: Redis, names: _Names) -> None:
        self._client, self._names = client, names

    async def get(self, org: uuid.UUID, key: str) -> bytes | None:
        name = self._names(org, "cache", check_name(key))
        try:
            value: object = await self._client.get(name)
        except _DOWN as error:  # a miss: the caller reads the source instead
            _log.warning("live cache read skipped: %s", type(error).__name__)
            return None
        return value if isinstance(value, bytes) else None

    async def set(self, org: uuid.UUID, key: str, value: bytes, ttl: timedelta) -> None:
        name, millis = self._names(org, "cache", check_name(key)), check_ttl(ttl)
        try:
            await self._client.set(name, value, px=millis)
        except _DOWN as error:
            _log.warning("live cache write skipped: %s", type(error).__name__)

    async def delete(self, org: uuid.UUID, key: str) -> None:
        name = self._names(org, "cache", check_name(key))
        try:
            await self._client.delete(name)
        except _DOWN as error:  # the entry lives on until its time to live ends
            _log.warning("live cache delete skipped: %s", type(error).__name__)


class RedisLimiter:
    def __init__(self, client: Redis, names: _Names) -> None:
        self._client, self._names = client, names

    async def hit(self, org: uuid.UUID, key: str, *, limit: int, window: timedelta) -> Hit:
        """A fixed window: INCR, PEXPIRE NX and PTTL in one MULTI, so the count and its expiry
        can never come apart (no Lua, so Valkey works too)."""
        name, millis = self._names(org, "limit", check_name(key)), check_ttl(window)
        check_limit(limit)
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incr(name)
                pipe.pexpire(name, millis, nx=True)
                pipe.pttl(name)
                count, _, remaining = await pipe.execute()
        except _DOWN as error:
            raise _unavailable() from error
        taken = int(count)
        left = timedelta(milliseconds=max(int(remaining), 0))
        return Hit(allowed=taken <= limit, count=taken, retry_after=left)


class RedisLock:
    def __init__(self, client: Redis, name: str, token: str) -> None:
        self._client, self._name, self._token = client, name, token.encode()

    async def _if_ours(self, act: Callable[[Pipeline], object]) -> bool:
        """Runs `act` only while the key still holds this lock's token (WATCH, compare, MULTI)."""
        async with self._client.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(self._name)
                current: object = await pipe.get(self._name)
                if current != self._token:
                    return False
                pipe.multi()
                act(pipe)
                results = await pipe.execute()
            except WatchError:  # changed between the compare and the act: no longer ours
                return False
        # 0 means the key was gone: a server that doesn't abort EXEC when a watched key expires
        # still says so here
        return bool(results[0])

    async def extend(self, ttl: timedelta) -> bool:
        millis = check_ttl(ttl)
        try:
            return await self._if_ours(lambda pipe: pipe.pexpire(self._name, millis))
        except _DOWN as error:  # a lock nobody can confirm is not held
            raise _unavailable() from error

    async def release(self) -> bool:
        try:
            return await self._if_ours(lambda pipe: pipe.delete(self._name))
        except _DOWN as error:  # its time to live frees it
            _log.warning("live lock release skipped: %s", type(error).__name__)
            return False


class RedisLocks:
    def __init__(self, client: Redis, names: _Names) -> None:
        self._client, self._names = client, names

    async def acquire(self, org: uuid.UUID, name: str, ttl: timedelta) -> RedisLock | None:
        key, millis = self._names(org, "lock", check_name(name)), check_ttl(ttl)
        token = secrets.token_hex(16)
        try:
            taken: object = await self._client.set(key, token, nx=True, px=millis)
        except _DOWN as error:
            raise _unavailable() from error
        return RedisLock(self._client, key, token) if taken else None


class RedisSubscription:
    def __init__(self, topic: str, pubsub: PubSub) -> None:
        self._topic, self._pubsub = topic, pubsub

    async def next(self, timeout: float) -> Event | None:
        try:
            message = await cast("_Messages", self._pubsub).get_message(
                ignore_subscribe_messages=True, timeout=timeout
            )
        except _DOWN as error:  # the subscriber re-reads state from the database
            raise _unavailable() from error
        if message is None:
            return None
        raw = message.get("data")
        data = decode_event(raw) if isinstance(raw, bytes | str) else None
        return None if data is None else Event(topic=self._topic, data=data)


async def _subscribed(pubsub: PubSub) -> None:
    """Waits for Redis to confirm the subscription, so nothing published after it is missed."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + _TIMEOUT
    while (left := deadline - loop.time()) > 0:
        message = await cast("_Messages", pubsub).get_message(timeout=left)
        if message is not None and message.get("type") == "subscribe":  # redis-py decodes it
            return
    raise _unavailable()


class RedisEvents:
    def __init__(self, client: Redis, names: _Names) -> None:
        self._client, self._names = client, names

    async def publish(self, org: uuid.UUID, topic: str, data: Mapping[str, object]) -> bool:
        channel, text = self._names(org, "events", check_topic(topic)), encode_event(data)
        try:
            await cast("_Untyped", self._client).publish(channel, text)
        except _DOWN as error:  # an event is a hint; the state it points to is in the database
            _log.warning("live event not sent: %s", type(error).__name__)
            return False
        return True

    @asynccontextmanager
    async def subscribe(self, org: uuid.UUID, topic: str) -> AsyncGenerator[RedisSubscription]:
        channel = self._names(org, "events", check_topic(topic))
        pubsub = cast("_Untyped", self._client).pubsub()
        try:
            try:
                await pubsub.subscribe(channel)
                await _subscribed(pubsub)
            except _DOWN as error:
                raise _unavailable() from error
            yield RedisSubscription(topic, pubsub)
        finally:
            try:
                await pubsub.aclose()
            except _DOWN as error:
                _log.warning("live subscription not closed cleanly: %s", type(error).__name__)


class RedisLive:
    """The live store on Redis (or Valkey): what an installation uses (FOURCE_REDIS_URL)."""

    backend = "redis"

    def __init__(self, url: str, *, prefix: str = "fource") -> None:
        try:
            where = parse_url(url)
        except ValueError:  # its own message could quote the URL, which holds the password
            raise ValueError(_NOT_A_URL) from None
        if not parse_qs(urlparse(url).query).keys() <= set(_QUERY_KEYS):
            raise ValueError(_OPTIONS)
        self._pool = ConnectionPool(
            **where,
            socket_connect_timeout=_TIMEOUT,
            socket_timeout=_TIMEOUT,
            health_check_interval=30,
            retry=Retry(NoBackoff(), 0),  # fail within the timeouts, never retry for long
        )
        self._client = Redis(connection_pool=self._pool)
        names = _Names(prefix)
        self.cache = RedisCache(self._client, names)
        self.limits = RedisLimiter(self._client, names)
        self.locks = RedisLocks(self._client, names)
        self.events = RedisEvents(self._client, names)

    async def ping(self) -> bool:
        try:
            return bool(await cast("_Untyped", self._client).ping())
        except _DOWN:
            return False

    async def close(self) -> None:
        await self._client.aclose()
        await self._pool.aclose()
