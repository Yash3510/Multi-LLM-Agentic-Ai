# fource-live

Live, short-lived shared state between 4CE's processes (master plan §6.3): live events, short caches, locks and rate limits. Everything is per organisation, and nothing is durable: jobs and run state live in the database ([`core/jobs`](../jobs/README.md)), so losing all of this loses no work.

**Owner:** R1 · **Decisions:** [ADR-0026](../../docs/adr/0026-redis-for-live-state.md)

Two backends: Redis when `FOURCE_REDIS_URL` is set, otherwise this process's own memory (`MemoryLive`), for development and tests, like SQLite for the database. With more than one process, set the URL. This package never imports the database.

## Public API

| Name | What it is |
| --- | --- |
| `Live` | The live store: `backend` (`"memory"` or `"redis"`), `cache`, `limits`, `ping()`, `close()` |
| `Cache` | `get(org, key)`, `set(org, key, value, ttl)`, `delete(org, key)`: bytes per organisation, each with a time to live from 1 ms to 24 hours. A cache holds copies; callers read the source on a miss |
| `RateLimiter`, `Hit` | `hit(org, key, limit=, window=)` counts an attempt in a fixed window and answers `Hit(allowed, count, retry_after)` |
| `LiveUnavailable` | The store can't be reached (503, `live_unavailable`); the message never carries its URL |
| `MemoryLive` | The in-process backend |
| `open_live(redis_url)`, `RedisLive(url, *, prefix="fource")` | The live store for `FOURCE_REDIS_URL`: Redis (or Valkey) when it is set, this process's memory when not. Redis keys are `<prefix>:<organisation>:<kind>:<name>`. Connects and answers within 2 seconds or counts as down: then the cache misses and drops writes, and the rate limiter raises `LiveUnavailable` (it fails closed). Messages and logs never carry the URL |

## Tests

The same contract tests run on every backend (the `live` fixture in `tests/conftest.py`).

```
uv run pytest core/live -m "not redis"
```

The Redis half runs only with `FOURCE_TEST_REDIS_URL` set to a Redis 8 server the tests may write to (`just test-redis`; CI's Redis job). Without it those tests fail; they never skip.
