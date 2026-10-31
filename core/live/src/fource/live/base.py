"""What the live store offers, whichever backend holds it (ADR-0026).

Everything here is short-lived and per organisation. Nothing is durable: a restart of the
store loses it all, and no work with it (jobs and run state live in the database).
"""

import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol

from fource.common import FourceError

MAX_TTL = timedelta(hours=24)
_NAME = re.compile(r"[A-Za-z0-9_.:-]{1,200}")


class LiveUnavailable(FourceError):
    """The live store can't be reached. The message never carries its URL."""

    code = "live_unavailable"
    status = 503


@dataclass(frozen=True)
class Hit:
    """One counted attempt: allowed while `count` is within the limit; `retry_after` is how long
    until the window's count starts again."""

    allowed: bool
    count: int
    retry_after: timedelta


def check_name(name: str) -> str:
    """A cache key, limit key or lock name: 1 to 200 letters, digits or `_.:-`."""
    if not _NAME.fullmatch(name):
        raise ValueError(f"a name is 1 to 200 letters, digits or _.:- : {name!r}")
    return name


def check_ttl(ttl: timedelta) -> int:
    """The time to live in whole milliseconds, from 1 ms to 24 hours: nothing here is meant to
    last."""
    millis = int(ttl / timedelta(milliseconds=1))
    if millis < 1 or ttl > MAX_TTL:
        raise ValueError(f"a time to live is from 1 ms to {MAX_TTL}: {ttl!r}")
    return millis


def check_limit(limit: int) -> int:
    if isinstance(limit, bool) or limit < 1:
        raise ValueError("a limit counts from 1")
    return limit


class Cache(Protocol):
    async def get(self, org: uuid.UUID, key: str) -> bytes | None: ...

    async def set(self, org: uuid.UUID, key: str, value: bytes, ttl: timedelta) -> None: ...

    async def delete(self, org: uuid.UUID, key: str) -> None: ...


class RateLimiter(Protocol):
    async def hit(self, org: uuid.UUID, key: str, *, limit: int, window: timedelta) -> Hit: ...


class Live(Protocol):
    """The services of the live store, on one backend: Redis, or this process's own memory."""

    @property
    def backend(self) -> str: ...

    @property
    def cache(self) -> Cache: ...

    @property
    def limits(self) -> RateLimiter: ...

    async def ping(self) -> bool: ...

    async def close(self) -> None: ...
