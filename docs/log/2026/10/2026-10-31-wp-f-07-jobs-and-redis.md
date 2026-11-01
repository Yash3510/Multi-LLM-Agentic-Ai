---
title: "The job queue and Redis"
type: log
status: implemented
owner: R1
updated: 2026-10-31
date: 2026-10-31
branch: 4ce-core
pr: null
work_package: "WP-F-07, WP-F-11"
author: Yash3510
areas: [core/jobs, core/live, core/identity, core/ledger, core/common, apps/server, .github/workflows, docs]
tags: [4ce, log, runtime, security]
---

# The job queue and Redis

## What changed

Backend slice 3, in 97 commits on `4ce-core` (`c2bbe6f` to `5dbd9c2` are the code, tests and ADRs; the docs commits follow them). Work was done task by task, each with a failing test first, a review, and a push once CI was green.

- **`core/jobs` (new):** a job queue per organisation in the database. `enqueue` runs in the caller's session, so a job commits with the state that needs it. A worker takes the oldest due job in one statement (`FOR UPDATE SKIP LOCKED` on PostgreSQL; SQLite's write lock serialises takers), holds it under a lease and a fresh `holder` token, runs the handler in the job's organisation session, and marks the job done in that same transaction only if the token still matches (`LeaseLost` otherwise, and the attempt's writes roll back). Failed attempts are retried after 30 s doubling to an hour, up to 5; a lost worker's job fails with "The last attempt did not finish" instead of running past `max_attempts`. A key keeps one unfinished job per organisation. Recurring jobs are keyed jobs (`recurring:<kind>`). On PostgreSQL a commit sends `NOTIFY fource_jobs` with an empty payload (NOTIFY ignores row-level security, so nothing about organisations may cross it) and workers LISTEN on a connection of their own; everything also polls every 2 s.
- **`core/live` (new):** live events, short caches, locks and rate limits, per organisation and short-lived, on Redis (or Valkey) when `FOURCE_REDIS_URL` is set and in the process's memory otherwise. Only this package imports Redis; it never imports the database. Cache and events fail open; the rate limiter and locks fail closed. Redis URLs are checked at start-up (only `db`, and `ssl_*` only on `rediss://`). No Lua. Events are at-most-once and in order for each subscriber; one that falls behind is told and then follows new events.
- **`apps/server`:** migration `0005` (the `jobs` table under row-level security, with `jobs_state`, `jobs_due` and `jobs_one_unfinished_per_key`); `fource-server worker [--once]` and `just worker` (the worker checks its database role as the server does, refuses to start with scheduled checkpoints on and no usable signing key, handles SIGINT and SIGTERM in two stages, and `--once` exits 1 when any attempt or organisation pass failed); scheduled ledger checkpoints (`ledger.checkpoint`) when `FOURCE_LEDGER_CHECKPOINT_MINUTES` is set; sign-in rate limit per client address before any password is checked (`FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE`, 30: 429 `rate_limited` with `Retry-After`, 503 `rate_limit_unavailable` when the limit cannot be checked); `/api/health` reports `redis` as `ok`, `unavailable` or `off`.
- **`core/identity`, `core/ledger`, `core/common`:** the `identity.signin.throttled` entry (one per throttle window, the client address kept only as a keyed hash, context `4ce-ledger-client-address-v1`); the two new settings.
- **Start-up role check (Task 1):** the PostgreSQL role check now also refuses a NOINHERIT member of the owner and any role that owns a table under row-level security (not only the ledger's). The worker runs the same check.
- **CI:** a Redis job (Redis 8.10.2 service, `just test-redis`).
- **Docs (this entry's commits):** new pages [jobs](../../../architecture/jobs.md) and [live state](../../../architecture/live.md); [API](../../../architecture/api.md), [database](../../../architecture/database.md), [identity](../../../architecture/identity.md), [ledger](../../../architecture/ledger.md), [repository](../../../architecture/repository.md), [licences](../../../architecture/licences.md), [services](../../../architecture/services.md) and the [overview](../../../architecture/overview.md) brought up to date; [state](../../../state.md); ADR-0014, ADR-0026 and ADR-0040.

## Why

Master plan §6.2 and §6.3 give 4CE a second process role and a queue whose jobs commit with run state, and Redis for what may be lost. Scheduled checkpoints (ADR-0014 point 8) and the sign-in rate limit that the ledger entry for failed sign-ins was waiting on both need them. The ledger is insert-only, so unthrottled failed sign-ins would grow it without bound.

## Files

| Path | Change |
| --- | --- |
| `core/jobs/` | New package: models, queue, worker loop, wake-ups, errors, tests, README |
| `core/live/` | New package: contract, in-process and Redis backends, tests, README |
| `core/identity/`, `core/ledger/`, `core/common/` | The throttled entry and its keyed hash; `EntryType.SIGNIN_THROTTLED`; the two settings |
| `apps/server/src/fource/server/` | `worker.py`, `scheduled.py`, `loops.py`, migration `0005`, the sign-in limit and health changes, `cli.py`, the shared role check |
| `apps/server/tests/` | Worker, scheduled, migration, role-check, API and PostgreSQL tests |
| `.github/workflows/`, `justfile`, `pyproject.toml`, `.env.example`, `uv.lock` | The Redis job, `just worker` and `just test-redis`, the layers and Redis contracts, the new settings, `redis` 8.1.0 |
| `docs/adr/0026-redis-for-live-state.md`, `0040-job-queue-on-postgresql.md` | New (proposed) |
| `docs/adr/0014-ledger-with-signed-checkpoints.md` | Scheduled checkpoints are built |
| `docs/architecture/jobs.md`, `live.md` | New pages |
| `docs/architecture/` (api, database, identity, ledger, repository, licences, services, overview, README), `docs/README.md`, `docs/state.md`, `core/jobs/README.md`, `core/live/README.md` | Brought up to date, indexed and linked |
| `docs/log/README.md`, this entry | The log row and entry |

## How it was verified

On `vps` (Debian, Python 3.12.15), 2026-10-31.

1. **Planner's evidence for Task 1 (labelled as the planner's, not re-run here):** the old role query, run with `-k refuses` against PostgreSQL 18.6, gave 2 failed, 3 passed; CI's PostgreSQL job passed with the new query (run 40285683734). On vps the unit RED for Task 1 was `uv run pytest apps/server/tests/test_role_check.py -q`: 2 failed, 1 passed, then 3 passed.
2. **CI on GitHub.** Run 41242147438 at `5dbd9c2` (the head of the code), all jobs green: `just check` on ubuntu-latest, windows-latest and macos-latest each `619 passed, 79 deselected`, the PostgreSQL job (`just test-postgres`) `39 passed, 659 deselected`, and the Redis job (`just test-redis`) `40 passed, 658 deselected`. Earlier runs per task: 40285683734 (`e42a7ee`, PostgreSQL 25), 41177593749 (`0b02fad`, 32), 41195801168 (`7b90a22`, 36), 41200663136 (`925cdfe`, 39), 41239571394 (`b068b8c`, all five jobs). The plan's counts (PostgreSQL 31, Redis 34) were the planner's arithmetic; the real counts are higher because review rounds added tests.
3. **Local PostgreSQL and Redis on throwaway containers on private ports** (the lead's decision Q4; the shared `services-postgres-1` and `services-redis-1` were never touched), after the docs commits, with PostgreSQL 18.6 on `127.0.0.1:55432` and Redis 8.10.2 on `127.0.0.1:56379`, both with throwaway passwords set in the environment:
   - `FOURCE_TEST_POSTGRES_PORT=55432 … uv run pytest -m postgres -q`: `39 passed, 659 deselected in 81.51s`.
   - `FOURCE_TEST_REDIS_URL=redis://127.0.0.1:56379/0 uv run pytest -m redis -q`: `40 passed, 658 deselected in 6.47s`.
   - Both containers were removed afterwards; `docker ps -a` showed no `fource-test-*` container.
   Each task's own RED and GREEN were recorded during the work and are not part of this entry.
4. **Fresh clone, SQLite, no Redis** (design "Done when" 2 and 3), `git clone --branch 4ce-core` of this checkout into a throwaway folder, deleted afterwards (the clone had the docs commits `aab1c6c`, `7078089` and `182974d` on top of `5dbd9c2`):
   - `just setup`: exit 0; `just migrate`: `The database is up to date.`
   - `create-user admin@example.com --role Admin` (password on stdin): `Created admin@example.com (Admin).`; `just ledger keygen` created the key and its public key under `data/ledger/`.
   - `FOURCE_SIGNIN_ATTEMPTS_PER_MINUTE=3 fource-server serve`: health `{"status":"ok","database":"ok","redis":"off"}`; four wrong-password sign-ins `401 401 401 429`; a fifth, with the right password, `HTTP/1.1 429 Too Many Requests` with `retry-after: 60`.
   - With the server stopped, `FOURCE_LEDGER_CHECKPOINT_MINUTES=60 fource-server worker --once`: `Ran 1 job attempt.`, exit 0.
   - `just ledger verify`: `Ledger of default: 6 entries, head 6.`, `A signed checkpoint vouches for it up to entry 5.`, `Verified.`, exit 0 (the user, three failures, one throttled entry, the checkpoint). No private key was printed.
5. **`just check`** at `fba59c0` (the docs commits in place; only this entry and its index row uncommitted): exit 0. `188 files already formatted`, ruff `All checks passed!`, pyright `0 errors, 0 warnings, 0 informations`, `Contracts: 12 kept, 0 broken.`, repo, neutrality and docs checks clean, `66 components checked`, `93 files scanned`, `5 bundled services checked`, gitleaks over the branch history passed, and the tests ended with `619 passed, 79 deselected in 86.26s (0:01:26)` (the 79 are the 39 PostgreSQL and 40 Redis tests, which need their servers; items 2 and 3). `real 2m20.888s`.
6. **Docs commits:** each passed the git hooks, including the docs check.

## Decisions

[ADR-0026](../../../adr/0026-redis-for-live-state.md) (Redis for live state; the sign-in rate limit) and [ADR-0040](../../../adr/0040-job-queue-on-postgresql.md) (the job queue), both proposed for R1 to accept; [ADR-0014](../../../adr/0014-ledger-with-signed-checkpoints.md) now records that scheduled checkpoints run in the worker when the operator sets `FOURCE_LEDGER_CHECKPOINT_MINUTES`. Decided by the project lead on 2026-10-26:

1. **Q1:** the sign-in limit fails closed (503 `rate_limit_unavailable` when it cannot be checked).
2. **Q2:** behind a proxy without `--forwarded-allow-ips`, every client shares one count; accepted and documented.
3. **Q3:** the Redis job in CI. AGENTS.md §3 reserves CI changes for humans; the lead's brief for this slice asked for this job and confirmed it, and the change is exactly that job.
4. **Q4:** throwaway PostgreSQL and Redis containers on private ports for local tests, never the shared services.

Also decided during review: the NOTIFY payload is empty (a ruling after the Task 7 review: NOTIFY ignores row-level security); `worker --once` exits 1 on any failed attempt or organisation pass; the worker refuses a superuser, `BYPASSRLS` or owner role like the server; the role check also refuses a NOINHERIT member of the owner (Task 1, the "role-check fix").

## New dependency

`redis` 8.1.0 (redis-py, the client of the bundled Redis): `License-Expression: MIT`, no runtime dependencies on Python 3.12, imported only in `core/live`. `fource-jobs` now depends on `psycopg` directly, approved by ADR-0037. fakeredis was not added ([licences](../../../architecture/licences.md)). `just licences` on 2026-10-31: 66 components checked, 93 files scanned, 5 bundled services checked, no problems.

## Docs updated

New: [jobs](../../../architecture/jobs.md), [live state](../../../architecture/live.md). Changed: [API](../../../architecture/api.md), [database](../../../architecture/database.md), [identity](../../../architecture/identity.md), [ledger](../../../architecture/ledger.md), [repository](../../../architecture/repository.md), [licences](../../../architecture/licences.md), [services](../../../architecture/services.md), [overview](../../../architecture/overview.md), the [architecture index](../../../architecture/README.md), the [docs index](../../../README.md), [state](../../../state.md), [ADR-0014](../../../adr/0014-ledger-with-signed-checkpoints.md), [ADR-0026](../../../adr/0026-redis-for-live-state.md), [ADR-0040](../../../adr/0040-job-queue-on-postgresql.md) and the READMEs of [`core/jobs`](../../../../core/jobs/README.md) and [`core/live`](../../../../core/live/README.md).

## Known limits and follow-ups

Issues aren't open yet (the GitHub project isn't set up); each item becomes one.

- **No heartbeats:** a handler must finish within its lease; one that doesn't may run twice, and only one run commits.
- **Finished jobs are kept;** no pruning and no priorities yet.
- **SQLite takes one job at a time,** and nothing wakes a worker but its poll.
- **The in-process live backend is one process's own;** with several processes set `FOURCE_REDIS_URL`.
- **Proxy addresses:** behind a proxy that hides client addresses, every client shares one sign-in count.
- **IPv6:** the limit counts the exact address, so a client can rotate within its /64; a later work package may count per /64.
- **A database error at the first refused attempt of a window** loses that window's throttled entry (the limit still holds).
- **Redis ACL users per purpose** (§8.1) are a follow-up for the bundled services.
- **PostgreSQL from a Windows host is untested.**
- **Neutrality terms in commit messages** are checked by no hook (reviewers check them).
