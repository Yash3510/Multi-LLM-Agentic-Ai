---
title: "Redis for live events, cache, locks and rate limits"
type: adr
status: planned
owner: R1
updated: 2026-10-26
covers: []
tags: [4ce, adr]
number: 26
decision_status: proposed
superseded_by: null
---

# ADR-0026: Redis for live events, cache, locks and rate limits

## Context

Master plan §2.7 and §6.3 put live events, short caches, distributed locks and login rate limits on Redis 8 (AGPL-3.0, run unmodified as a separate service, reached through the MIT-licensed redis-py client). Jobs and run state stay in PostgreSQL ([ADR-0040](0040-job-queue-on-postgresql.md)), so a Redis restart loses no work, and Valkey is a drop-in replacement. §7.24 and §8.2 rule 10 keep caches apart per organisation. 4CE also runs with no setup on SQLite, with no Redis either. An account is locked for 15 minutes after 5 failed sign-ins, counted in the database ([ADR-0038](0038-signed-tokens-for-sign-in.md)).

## Decision

1. **A `core/live` package** owns the four services behind its own interface: `Live`, with `cache`, `limits`, `locks`, `events`, `ping` and `close`. Only its Redis backend imports Redis, and the package never imports the database.
2. **Two backends:** Redis when `FOURCE_REDIS_URL` is set, otherwise the process's own memory, for development and tests. With several processes, an installation sets the URL.
3. **Everything is per organisation and short-lived:** keys and channels are `<prefix>:<organisation>:<kind>:<name>`, and every key lives at most 24 hours. Redis is not backed up.
4. **When Redis can't be reached:** the cache misses and drops writes, and publishing an event returns false (both fail open: they are hints over what the database holds). The rate limit and taking or extending a lock raise `LiveUnavailable` (they fail closed). A lock that can't be released frees itself when its time runs out.
5. **Locks save work; they don't guard correctness:** `SET NX PX` with a random token; release and extend compare the token inside `WATCH` and `MULTI`. No fencing tokens: anything whose correctness needs mutual exclusion uses PostgreSQL.
6. **The rate limiter** counts in a fixed window: `INCR`, `PEXPIRE NX` and `PTTL` in one `MULTI`. No Lua, so Valkey works and no `EVAL` right is needed.
7. **Events** use Redis pub/sub: a JSON object per event, with no replay. A subscriber reads state from the database first, then follows events. Events carry ids and short fields, never document content or secrets.
8. **The sign-in rate limit** runs in the sign-in route before any password is checked or anything is written: `FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE` (default 30) attempts per client address per minute. Over it, the answer is 429 `rate_limited` with `Retry-After`. If the limit can't be checked, it is 503 `rate_limit_unavailable`: it fails closed, and existing sessions are unaffected. The project lead confirmed this on 2026-10-26. The per-account lockout is unchanged and applies to every attempt let through.
9. **One ledger entry per throttle window:** the attempt that first goes over the limit writes `identity.signin.throttled` (actor `anonymous`; refs `limit` and `until`; `inputs_sha256` the HMAC-SHA256 of the client address under a key derived from `FOURCE_SECRET_KEY` with the context `4ce-ledger-client-address-v1`, as for unknown emails in [ADR-0039](0039-every-action-writes-a-ledger-entry.md)). Later refusals in the window write nothing, so a flood can't flood the ledger.
10. **Health** reports `redis` as `ok`, `unavailable` or `off` (none configured), and answers 503 when a configured Redis can't be reached.
11. **Proxies:** the limit counts the address the server sees. Without a configured proxy setting every client behind one proxy shares one address and one limit. The project lead accepted this on 2026-10-26; the consequences below record it.
12. **Tests and CI:** the contract tests run against the in-process backend everywhere and against real Redis in a CI job of its own. The project lead approved adding that job on 2026-10-26 (AGENTS.md §3 reserves CI changes for humans). Locally, tests may use a throwaway Redis on a private port, never the shared service.

## Alternatives considered

| Option | Why not |
| --- | --- |
| fakeredis for tests | Licence-clean (BSD-3-Clause, with sortedcontainers under Apache-2.0), but the tests would check an emulation. The in-process backend is product code and passes the same contract tests that real Redis passes in CI |
| Lua scripts | `MULTI` and `WATCH` do the same here without the `EVAL` right |
| Redis Streams for events | No replay is needed: run state is in the database |
| Fencing tokens | A counter in a store that may lose everything doesn't only go up |
| A rate limit that fails open | Would leave only the lockout during an outage, and "could not check" is never a pass (§6.1.5). It is one line to change if the lead prefers availability |
| A limit per email | The lockout already covers known accounts; a limit per address also covers guessing across many accounts |
| An entry for every refused attempt | Would turn a flood into ledger writes contending for the head row |

## Consequences

- With no Redis configured, each process counts, locks and publishes on its own: fine for development only.
- Behind a proxy that doesn't pass the client's address on (Uvicorn's `--forwarded-allow-ips`), every client shares one limit.
- While Redis is down, new sign-ins are refused (503) and `/api/health` says so.
- Redis ACL users per purpose (§8.1) are a follow-up for the bundled services.

## Status

Proposed on 2026-10-26, decided by the project lead ("follow the master plan"). On 2026-10-26 the lead also confirmed the fail-closed sign-in limit, accepted the shared limit behind an unconfigured proxy, and approved the Redis CI job. To be accepted by R1.
