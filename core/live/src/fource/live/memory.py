"""The in-process backend: this process's own dictionaries (ADR-0026).

For development and tests, like SQLite for the database. Each process has its own cache,
counts, locks and events, so an installation with more than one process sets FOURCE_REDIS_URL.
"""

import asyncio
import secrets
import time
import uuid
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from datetime import timedelta

from fource.live.base import (
    Event,
    Hit,
    LiveUnavailable,
    check_limit,
    check_name,
    check_org,
    check_topic,
    check_ttl,
    decode_event,
    encode_event,
)

_Slot = tuple[uuid.UUID, str]
_PURGE_AT = 1000  # entries; expired ones are dropped when a write finds this many
_QUEUE_SIZE = 1000  # events a slow subscriber may fall behind before it is cut off


def _clock() -> float:
    return time.monotonic()


def _purge[V](items: dict[_Slot, tuple[V, float]]) -> None:
    if len(items) >= _PURGE_AT:
        current = _clock()
        for slot in [slot for slot, (_, ends) in items.items() if ends <= current]:
            del items[slot]


class MemoryCache:
    def __init__(self) -> None:
        self._items: dict[_Slot, tuple[bytes, float]] = {}

    async def get(self, org: uuid.UUID, key: str) -> bytes | None:
        slot = (check_org(org), check_name(key))
        item = self._items.get(slot)
        if item is None or item[1] <= _clock():
            self._items.pop(slot, None)
            return None
        return item[0]

    async def set(self, org: uuid.UUID, key: str, value: bytes, ttl: timedelta) -> None:
        slot, millis = (check_org(org), check_name(key)), check_ttl(ttl)
        _purge(self._items)
        self._items[slot] = (value, _clock() + millis / 1000)

    async def delete(self, org: uuid.UUID, key: str) -> None:
        self._items.pop((check_org(org), check_name(key)), None)


class MemoryLimiter:
    def __init__(self) -> None:
        self._windows: dict[_Slot, tuple[int, float]] = {}

    async def hit(self, org: uuid.UUID, key: str, *, limit: int, window: timedelta) -> Hit:
        slot, millis = (check_org(org), check_name(key)), check_ttl(window)
        check_limit(limit)
        current = _clock()
        count, ends = self._windows.get(slot, (0, current))
        if ends <= current:
            _purge(self._windows)
            count, ends = 0, current + millis / 1000
        count += 1
        self._windows[slot] = (count, ends)
        left = timedelta(seconds=ends - current)
        return Hit(allowed=count <= limit, count=count, retry_after=left)


class MemoryLock:
    def __init__(self, held: dict[_Slot, tuple[str, float]], slot: _Slot, token: str) -> None:
        self._held, self._slot, self._token = held, slot, token

    def _ours(self) -> bool:
        item = self._held.get(self._slot)
        return item is not None and item[0] == self._token and item[1] > _clock()

    async def extend(self, ttl: timedelta) -> bool:
        millis = check_ttl(ttl)
        if not self._ours():
            return False
        self._held[self._slot] = (self._token, _clock() + millis / 1000)
        return True

    async def release(self) -> bool:
        if not self._ours():
            return False
        del self._held[self._slot]
        return True


class MemoryLocks:
    def __init__(self) -> None:
        self._held: dict[_Slot, tuple[str, float]] = {}

    async def acquire(self, org: uuid.UUID, name: str, ttl: timedelta) -> MemoryLock | None:
        slot, millis = (check_org(org), check_name(name)), check_ttl(ttl)
        item = self._held.get(slot)
        if item is not None and item[1] > _clock():
            return None
        _purge(self._held)
        token = secrets.token_hex(16)
        self._held[slot] = (token, _clock() + millis / 1000)
        return MemoryLock(self._held, slot, token)


class MemorySubscription:
    def __init__(self, topic: str) -> None:
        self._topic = topic
        self._queue: asyncio.Queue[str] = asyncio.Queue(maxsize=_QUEUE_SIZE)
        self._missed = False

    def deliver(self, text: str) -> None:
        if self._queue.full():  # one that doesn't keep up is cut off, as on Redis
            self._missed = True
        else:
            self._queue.put_nowait(text)

    async def next(self, timeout: float) -> Event | None:
        """Waits the whole timeout for an event; text that isn't a JSON object is skipped. A
        subscriber that missed events gets LiveUnavailable once, loses what was buffered, and
        re-reads the state; the same subscription then follows new events."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            if self._missed:
                self._missed = False  # then it follows new events, as a reconnected Redis one does
                while not self._queue.empty():
                    self._queue.get_nowait()
                raise LiveUnavailable("A subscriber fell too far behind and missed events.")
            try:
                text = await asyncio.wait_for(self._queue.get(), max(deadline - loop.time(), 0))
            except TimeoutError:
                return None
            data = decode_event(text)
            if data is not None:
                return Event(topic=self._topic, data=data)


class MemoryEvents:
    def __init__(self) -> None:
        self._subscribers: dict[_Slot, set[MemorySubscription]] = {}

    async def publish(self, org: uuid.UUID, topic: str, data: Mapping[str, object]) -> bool:
        slot = (check_org(org), check_topic(topic))
        text = encode_event(data)  # as JSON, so subscribers get what Redis would give them
        for subscription in self._subscribers.get(slot, set()):
            subscription.deliver(text)
        return True

    @asynccontextmanager
    async def subscribe(self, org: uuid.UUID, topic: str) -> AsyncGenerator[MemorySubscription]:
        slot = (check_org(org), check_topic(topic))
        subscription = MemorySubscription(topic)
        self._subscribers.setdefault(slot, set()).add(subscription)
        try:
            yield subscription
        finally:
            subscribers = self._subscribers.get(slot, set())
            subscribers.discard(subscription)
            if not subscribers:
                self._subscribers.pop(slot, None)


class MemoryLive:
    """One process's live store: for development and tests (no FOURCE_REDIS_URL)."""

    backend = "memory"

    def __init__(self) -> None:
        self.cache = MemoryCache()
        self.limits = MemoryLimiter()
        self.locks = MemoryLocks()
        self.events = MemoryEvents()

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None
