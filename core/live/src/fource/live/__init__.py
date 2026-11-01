"""Live, short-lived shared state: events, cache, locks and rate limits, on Redis or (for
development) in this process (ADR-0026). Nothing here is durable."""

from fource.live.base import (
    Cache,
    Event,
    Events,
    HeldLock,
    Hit,
    Live,
    LiveUnavailable,
    Locks,
    RateLimiter,
    Subscription,
)
from fource.live.memory import MemoryLive
from fource.live.redis_store import RedisLive, RedisLock, check_redis_url


def open_live(redis_url: str | None, *, prefix: str = "fource") -> Live:
    """Redis when FOURCE_REDIS_URL is set; otherwise this process's own memory."""
    return MemoryLive() if redis_url is None else RedisLive(redis_url, prefix=prefix)


__all__ = [
    "Cache",
    "Event",
    "Events",
    "HeldLock",
    "Hit",
    "Live",
    "LiveUnavailable",
    "Locks",
    "MemoryLive",
    "RateLimiter",
    "RedisLive",
    "RedisLock",
    "check_redis_url",
    "Subscription",
    "open_live",
]
