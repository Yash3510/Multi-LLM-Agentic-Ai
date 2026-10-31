"""What the live store offers, whichever backend holds it (ADR-0026).

Everything here is short-lived and per organisation. Nothing is durable: a restart of the
store loses it all, and no work with it (jobs and run state live in the database).
"""

import json
import re
import uuid
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, cast

from fource.common import FourceError

MAX_TTL = timedelta(hours=24)
_NAME = re.compile(r"[A-Za-z0-9_.:-]{1,200}")
_TOPIC = re.compile(r"[a-z0-9][a-z0-9_.:-]{0,199}")


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


@dataclass(frozen=True)
class Event:
    topic: str
    data: Mapping[str, object]


def check_name(name: str) -> str:
    """A cache key, limit key or lock name: 1 to 200 letters, digits or `_.:-`."""
    if not _NAME.fullmatch(name):
        raise ValueError(f"a name is 1 to 200 letters, digits or _.:- : {name!r}")
    return name


def check_org(org: object) -> uuid.UUID:
    """The organisation as a UUID, or ValueError. Typed `object` so the check is real: a text
    could hold `:` or a glob, and a key must be built from the UUID alone, never from whatever
    a caller passed."""
    if not isinstance(org, uuid.UUID):
        raise ValueError("an organisation is identified by a UUID")
    return org


def check_topic(topic: str) -> str:
    """An event topic: lower case, digits and `_.:-`, such as `run.<id>`."""
    if not _TOPIC.fullmatch(topic):
        raise ValueError(f"a topic is lower case, digits and _.:- : {topic!r}")
    return topic


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


def encode_event(data: Mapping[str, object]) -> str:
    """An event's data as JSON text; ValueError for anything JSON can't hold."""
    try:
        return json.dumps(dict(data), allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError, RecursionError) as error:
        raise ValueError("an event's data is a JSON object") from error


def decode_event(text: str | bytes) -> dict[str, object] | None:
    """The data of a received event, or None for anything that isn't a JSON object."""
    try:
        data: object = json.loads(text)
    except (ValueError, RecursionError):
        return None
    return cast("dict[str, object]", data) if isinstance(data, dict) else None


class Cache(Protocol):
    async def get(self, org: uuid.UUID, key: str) -> bytes | None: ...

    async def set(self, org: uuid.UUID, key: str, value: bytes, ttl: timedelta) -> None: ...

    async def delete(self, org: uuid.UUID, key: str) -> None: ...


class RateLimiter(Protocol):
    async def hit(self, org: uuid.UUID, key: str, *, limit: int, window: timedelta) -> Hit: ...


class HeldLock(Protocol):
    async def extend(self, ttl: timedelta) -> bool: ...

    async def release(self) -> bool: ...


class Locks(Protocol):
    async def acquire(self, org: uuid.UUID, name: str, ttl: timedelta) -> HeldLock | None: ...


class Subscription(Protocol):
    async def next(self, timeout: float) -> Event | None: ...


class Events(Protocol):
    async def publish(self, org: uuid.UUID, topic: str, data: Mapping[str, object]) -> bool: ...

    def subscribe(
        self, org: uuid.UUID, topic: str
    ) -> AbstractAsyncContextManager[Subscription]: ...


class Live(Protocol):
    """The services of the live store, on one backend: Redis, or this process's own memory."""

    @property
    def backend(self) -> str: ...

    @property
    def cache(self) -> Cache: ...

    @property
    def limits(self) -> RateLimiter: ...

    @property
    def locks(self) -> Locks: ...

    @property
    def events(self) -> Events: ...

    async def ping(self) -> bool: ...

    async def close(self) -> None: ...
