---
title: Jobs
type: architecture
status: active
owner: R1
updated: 2026-11-01
covers:
  - core/jobs/
  - apps/server/src/fource/server/worker.py
  - apps/server/src/fource/server/scheduled.py
tags: [4ce, architecture, runtime, server]
---

# Jobs

How 4CE does work outside a request: a job queue in the database, and the worker process that runs it. The code is [`core/jobs`](../../core/jobs/README.md); the worker command is [`worker.py`](../../apps/server/src/fource/server/worker.py) and the scheduled checkpoint [`scheduled.py`](../../apps/server/src/fource/server/scheduled.py).

## Queuing a job

- `enqueue(session, kind, payload=, run_at=, key=, max_attempts=)` runs in the caller's organisation session, so the job commits with the state that needs it, or not at all (master plan §6.3).
- A `kind` is lower-case and dotted (`ledger.checkpoint`). A `payload` is a JSON object of at most 16 KiB holding ids and small parameters, never document content or secrets.
- A `key` keeps at most one unfinished job per organisation: queuing a key that is still queued or running returns that job.
- On PostgreSQL the commit wakes listening workers (`NOTIFY fource_jobs`). The payload is empty: NOTIFY is per database and row-level security does not apply to it, so nothing about organisations crosses the channel.

## The jobs table

`jobs` (migration `0005`) belongs to one organisation per row and is under row-level security like every table ([database](database.md#row-level-security)). A job is `queued`, `running`, `done` or `failed`, with `run_at` (not before), `attempts` and `max_attempts`, a lease (`locked_until`) and the `holder` token of the worker that holds it, `last_error` and `finished_at`.

## How a worker runs a job

1. **Take.** One statement takes the organisation's oldest due job and holds it for a lease under a fresh holder token, and commits. PostgreSQL skips rows other workers hold (`FOR UPDATE SKIP LOCKED`); SQLite has no row locks, but its write lock lets one worker take a job at a time.
2. **Run.** The handler runs in the job's organisation session, and the job is marked `done` in the same transaction, only if the holder token still matches. A worker whose lease ran out and whose job another worker took finds no match, and its attempt's writes roll back: a job runs at least once, and its database effects commit at most once.
3. **Fail.** A failed attempt is queued again after 30 seconds, doubling up to an hour, until `max_attempts` (5); then the job is `failed`. Only a `FourceError`'s message or the error's class name is kept in `last_error`, cut to 1000 characters.
4. **Lost workers.** A `running` job whose lease ran out can be taken again; if that would pass `max_attempts`, it fails with "The last attempt did not finish" instead.

A worker visits every organisation in turn. On PostgreSQL it LISTENs on a connection of its own and also polls every 2 seconds; SQLite only polls.

## Recurring and scheduled jobs

A recurring job is an ordinary job with the key `recurring:<kind>`: at the start of each pass the worker keeps one queued in every organisation, due one interval after the last one finished.

**Scheduled checkpoints** are the first: when `FOURCE_LEDGER_CHECKPOINT_MINUTES` is set (1 to 525600; off by default), the worker signs each organisation's ledger head that often with the installation key ([ledger](ledger.md#checkpoints-and-the-key)). Setting it is the operator's decision to let the worker sign ([ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md) point 8); unset, nothing is signed. Each one writes the same `checkpoint` entry and file as `just ledger checkpoint`, the file before its commit, so every file signs an entry that exists. An empty ledger is left alone, and so is an idle one: when the newest entry is already a checkpoint made with the installation key there is nothing new to vouch for, so the job completes without signing (a hand-run `just ledger checkpoint` always signs). The file is written atomically ([ledger](ledger.md#checkpoints-and-the-key)), so a failed write leaves none behind. A file already there for the same entry (an earlier attempt's) is kept; one that signs another hash for that entry fails the job with "the chain may have been cut"; one that exists but can't be read as a checkpoint fails it with "unreadable checkpoint file …". Either way, run `just ledger verify`.

## The worker command

`fource-server worker [--once]` (`just worker`) checks its database role as the server does and refuses a superuser, a `BYPASSRLS` role or a table owner ([database](database.md#row-level-security)), loads the signing key if checkpoints are on (and refuses to start without a usable one), then runs until stopped. `--once` runs the jobs that are due and exits, printing how many attempts it made; it exits 1 when any attempt or any organisation's pass failed, so cron and scripts can tell. The first SIGINT or SIGTERM lets the running job finish; a second stops at once. On Windows, Ctrl+C stops at once. A database that isn't migrated says to run `just migrate`.

## Known limits

- **No heartbeats:** a handler must finish within its lease (2 minutes for the checkpoint). One that doesn't may run twice; only one run commits, and effects outside the database (files) must be safe to repeat.
- **Finished jobs are kept;** there is no pruning and no priority yet.
- **SQLite:** one worker takes a job at a time, and nothing wakes a worker but its poll.
- **One query per organisation per pass,** to look for work.
- **PostgreSQL from a Windows host is untested** ([database](database.md#known-limits)).

## Decisions

[ADR-0040](../adr/0040-job-queue-on-postgresql.md) (the queue), [ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md) (who signs checkpoints), [ADR-0010](../adr/0010-modular-monolith-on-one-database.md) point 5 (what needs PostgreSQL).

## Acceptance

On SQLite: `core/jobs/tests/` (each job taken once by five takers, a handler's writes commit with its job, a lost lease rolls back) and `apps/server/tests/test_scheduled.py`. On PostgreSQL, in CI's PostgreSQL job: `apps/server/tests/test_postgres.py` (jobs per organisation under row-level security, `SKIP LOCKED` with five takers and past a row another transaction holds, two staggered workers run a recurring interval once, a NOTIFY wakes a listener).
