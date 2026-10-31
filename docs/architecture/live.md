---
title: Live state
type: architecture
status: active
owner: R1
updated: 2026-10-31
covers:
  - core/live/
tags: [4ce, architecture, deploy, security]
---

# Live state

Live events, short caches, locks and rate limits that 4CE's processes share. The code is [`core/live`](../../core/live/README.md); the Redis service is on the [bundled services](services.md) page.

## Backends

- **Redis** (or Valkey) when `FOURCE_REDIS_URL` is set: what an installation uses. `.env.example` shows `redis://:${FOURCE_REDIS_PASSWORD}@localhost:6379/0`, commented out like the PostgreSQL URLs.
- **This process's memory** otherwise: for development and tests, like SQLite for the database. With more than one process (several server workers, or a worker beside the server), each would have its own, so set the URL.
- `/api/health` reports `"redis": "ok"`, `"unavailable"` (and answers 503) or `"off"` (no URL).
- **The URL's options are checked at start-up.** Only `db` may be set on `redis://` and `unix://`; the `ssl_*` trust settings (`ssl_cert_reqs`, `ssl_ca_certs`, `ssl_certfile`, `ssl_keyfile`, `ssl_check_hostname`) only on `rediss://`; anything else, including the timeouts the pool sets itself, is refused.

## What it holds

Nothing durable: jobs and run state are in the database ([jobs](jobs.md)), so losing all of this loses no work, and Redis is not backed up. Everything is per organisation (master plan §7.24, §8.2 rule 10).

| Service | What | Redis key | When Redis is down |
| --- | --- | --- | --- |
| Cache | Bytes with a time to live from 1 ms to 24 hours | `fource:<org>:cache:<key>` | A miss; writes are dropped (fails open) |
| Rate limits | A count per key in a fixed window (`INCR`, `PEXPIRE NX`, `PTTL` in one `MULTI`) | `fource:<org>:limit:<key>` | `LiveUnavailable` (fails closed) |
| Locks | One holder per name, with a random token and a time to live | `fource:<org>:lock:<name>` | Taking or extending raises `LiveUnavailable` (fails closed); releasing returns false and the time to live frees it |
| Events | Pub/sub of JSON objects, no replay | channel `fource:<org>:events:<topic>` | Publishing returns false (fails open); subscribing raises `LiveUnavailable` |

## Rules for code that uses it

- **A cache holds copies.** Read the source on a miss, and never consult a cache before a policy check (§8.2 rule 1).
- **Locks save work; they don't guard correctness.** There are no fencing tokens: mutual exclusion that matters uses the database, as the job queue does.
- **Events say "look again".** A subscriber reads the state from the database first, then follows events; events carry ids and short fields, never document content or secrets.
- **Delivery is best effort:** at-most-once, in order for each subscriber. `publish` returning true means only that the store took the event. A subscriber that falls too far behind (Redis cuts it off; the in-process backend after 1000 unread events) is told with `LiveUnavailable` from its next `next()`, must read the state again, and then follows new events.

## The sign-in rate limit

- Every sign-in is counted against its client address before any password is checked or anything is written: `FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE` (30) a minute.
- Over the limit, the answer is 429 `rate_limited` with a `Retry-After` header. The attempt that first goes over writes one `identity.signin.throttled` ledger entry per window ([identity](identity.md#ledger)).
- If the limit can't be checked (Redis is down), sign-in answers 503 `rate_limit_unavailable`: it fails closed. Existing sessions keep working.
- The per-account lockout (5 failures, 15 minutes) is unchanged and applies to every attempt let through ([identity](identity.md#lockout)).
- **The limit is per exact client address,** so an IPv6 client can rotate through the addresses of its own /64 and escape it. A later work package may count per /64.
- **Behind a proxy,** let Uvicorn see the client's address (`--forwarded-allow-ips`, see [API](api.md#running-it)), or every client shares one count, and a flood from one blocks everyone's sign-in for a minute.

## Connecting

The client connects and answers within 2 seconds or counts Redis as down, and never retries for long, so a down Redis can't stall a sign-in. No message or log carries the URL, which holds the password. No Lua is used, so Valkey works and no `EVAL` right is needed.

## Testing

The same contract tests run on both backends. The Redis half needs `FOURCE_TEST_REDIS_URL`, a Redis 8 server the tests may write to: CI's Redis job provides one (`just test-redis`). Without it those tests fail, never skip. Never point it at a shared server; locally, start a throwaway Redis on a private port and point the variable at that.

## Known limits

- The in-process backend is one process's own.
- Redis ACL users per purpose (§8.1) are a follow-up for the bundled services; the compose file sets a password for the default user.
- Behind a proxy that hides client addresses, there is one shared count (above); an IPv6 client can rotate within a /64 (above).

## Decisions

[ADR-0026](../adr/0026-redis-for-live-state.md).
