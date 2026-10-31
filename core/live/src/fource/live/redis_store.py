"""The Redis backend (ADR-0026). Every key and channel is `<prefix>:<org>:<kind>:<name>`.

When Redis can't be reached: the cache misses and drops writes, and the rate limiter raises
LiveUnavailable (it fails closed). No message carries the URL, which holds the password.
"""

import logging
import uuid
from datetime import timedelta
from typing import Protocol, cast

from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.connection import parse_url
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff
from redis.exceptions import RedisError

from fource.live.base import (
    Hit,
    LiveUnavailable,
    check_limit,
    check_name,
    check_ttl,
)

_log = logging.getLogger("fource.live")
_DOWN = (RedisError, OSError)
_TIMEOUT = 2.0  # seconds to connect or to answer: a down Redis must not stall a sign-in
_NOT_A_URL = "FOURCE_REDIS_URL is not a redis://, rediss:// or unix:// URL"


class _Untyped(Protocol):
    """The client calls whose redis-py signatures leave `**kwargs` untyped, as used here."""

    async def ping(self) -> bool: ...


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


class RedisLive:
    """The live store on Redis (or Valkey): what an installation uses (FOURCE_REDIS_URL)."""

    backend = "redis"

    def __init__(self, url: str, *, prefix: str = "fource") -> None:
        try:
            where = parse_url(url)
        except ValueError:  # its own message could quote the URL, which holds the password
            raise ValueError(_NOT_A_URL) from None
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

    async def ping(self) -> bool:
        try:
            return bool(await cast("_Untyped", self._client).ping())
        except _DOWN:
            return False

    async def close(self) -> None:
        await self._client.aclose()
        await self._pool.aclose()
