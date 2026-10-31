"""The in-process backend: this process's own dictionaries (ADR-0026).

For development and tests, like SQLite for the database. Each process has its own cache,
counts, locks and events, so an installation with more than one process sets FOURCE_REDIS_URL.
"""

import time
import uuid
from datetime import timedelta

from fource.live.base import Hit, check_limit, check_name, check_ttl

_Slot = tuple[uuid.UUID, str]
_PURGE_AT = 1000  # entries; expired ones are dropped when a write finds this many


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
        slot = (org, check_name(key))
        item = self._items.get(slot)
        if item is None or item[1] <= _clock():
            self._items.pop(slot, None)
            return None
        return item[0]

    async def set(self, org: uuid.UUID, key: str, value: bytes, ttl: timedelta) -> None:
        slot, millis = (org, check_name(key)), check_ttl(ttl)
        _purge(self._items)
        self._items[slot] = (value, _clock() + millis / 1000)

    async def delete(self, org: uuid.UUID, key: str) -> None:
        self._items.pop((org, check_name(key)), None)


class MemoryLimiter:
    def __init__(self) -> None:
        self._windows: dict[_Slot, tuple[int, float]] = {}

    async def hit(self, org: uuid.UUID, key: str, *, limit: int, window: timedelta) -> Hit:
        slot, millis = (org, check_name(key)), check_ttl(window)
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


class MemoryLive:
    """One process's live store: for development and tests (no FOURCE_REDIS_URL)."""

    backend = "memory"

    def __init__(self) -> None:
        self.cache = MemoryCache()
        self.limits = MemoryLimiter()

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        return None
