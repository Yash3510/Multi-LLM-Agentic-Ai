---
title: "Job queue on PostgreSQL"
type: adr
status: planned
owner: R1
updated: 2026-10-26
covers: []
tags: [4ce, adr]
number: 40
decision_status: proposed
superseded_by: null
---

# ADR-0040: Job queue on PostgreSQL

## Context

Master plan §6.3 chooses 4CE's own job queue on PostgreSQL `SELECT … FOR UPDATE SKIP LOCKED`, whose jobs commit in the same transaction as run state, so a Redis restart loses no work; §6.2 gives 4CE a second process role, the worker. [ADR-0010](0010-modular-monolith-on-one-database.md) point 5 says features that need PostgreSQL say so: development runs on SQLite, which has neither `SKIP LOCKED` nor LISTEN/NOTIFY. Every table belongs to one organisation under row-level security (§7.24). [ADR-0014](0014-ledger-with-signed-checkpoints.md) point 8 lets a scheduled job sign ledger checkpoints once the queue lands.

## Decision

1. **A `core/jobs` package** owns the queue and the worker loop. In the layers contract it sits below `core/identity` and above `core/live`, `core/ledger` and `core/db`. The worker process is `fource-server worker`, in `apps/server`.
2. **One `jobs` table, per organisation, under row-level security.** Work that concerns every organisation (a checkpoint) is one job per organisation. A worker takes inside one organisation session at a time and visits each organisation in turn.
3. **Take, then work.** One statement takes the oldest due job, `UPDATE … WHERE id = (SELECT … FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING …`, setting it `running` with a lease (`locked_until`) and a fresh `holder`, and commits at once. SQLite drops the clause; the statement writes before it reads, so SQLite's write lock lets one worker take a job at a time.
4. **The work and its completion commit together.** The handler runs in the job's organisation session, and the job is marked `done` in that same transaction by an UPDATE conditioned on its `holder`. If another worker took the job over after the lease ran out, the UPDATE finds nothing, the worker raises `LeaseLost` and the attempt's writes roll back. Jobs run at least once; their database effects commit at most once. Effects outside the database, such as files, must be safe to repeat.
5. **States** are `queued`, `running`, `done` and `failed`. A failed attempt is queued again after 30 seconds, doubling up to an hour, until `max_attempts` (default 5), then `failed`. A `running` job whose lease ran out can be taken again; taken beyond `max_attempts`, it fails without running. A handler's lease must be longer than its longest run; there are no heartbeats yet.
6. **An idempotency key:** at most one unfinished job per organisation and key (a partial unique index). Queuing a key that is pending returns the pending job.
7. **Recurring jobs** are ordinary jobs with the key `recurring:<kind>`: the worker keeps one queued in each organisation, due one interval after the last one finished.
8. **Wake-ups:** queuing a job sends `pg_notify('fource_jobs', <organisation>)` in its transaction; workers LISTEN on a connection of their own and also poll every 2 seconds. SQLite only polls.
9. **Shutdown:** the first SIGINT or SIGTERM stops taking and lets the running job finish; a second stops at once, and that job's transaction rolls back.
10. **What is kept of an error** is a `FourceError`'s message, or only the error's class name: other messages can quote documents, statements or URLs.
11. **The queue writes no ledger entries of its own.** Enqueue, take and retry are plumbing; the actions are the handlers', and each records itself in the job's transaction.
12. **Scheduled checkpoints** (kind `ledger.checkpoint`) run only when the operator sets `FOURCE_LEDGER_CHECKPOINT_MINUTES`: that setting is the human decision ADR-0014 point 8 allows. Each writes the existing `checkpoint` entry, and the same file as `ledger checkpoint` before its commit. A file already there for the same entry is kept (a retry); one that signs another hash fails the job, because the chain may have been cut.

## Alternatives considered

| Option | Why not |
| --- | --- |
| A queue library or a message broker | The master plan chose its own queue, in the same database and transaction as run state; a broker is another service that can lose work |
| Holding the row lock for the whole job | A long job would keep a transaction open, and on SQLite the write lock for everyone |
| A queue table outside row-level security, or a take function that bypasses it | Breaks §7.24's rule, or adds a path with the owner's rights; visiting organisations in turn costs one query per organisation per pass |
| A schedules table | A recurring job as a keyed job needs no second table, and two workers can't both queue it |
| Ledger entries for enqueue, take and retry | Plumbing, not actions; they would flood each organisation's chain and contend for its head row |

## Consequences

- On SQLite one worker takes a job at a time, and nothing wakes a worker but its poll: correct, and enough for development.
- A worker sends one query per organisation per pass to look for work.
- Finished jobs are kept; pruning them is future work, like priorities and heartbeats (with the run store, WP-RT-01).
- A handler that outlives its lease may run twice; only one of the runs commits.

## Status

Proposed on 2026-10-26, decided by the project lead ("follow the master plan"; scheduled checkpoints approved on 2026-10-24). To be accepted by R1.
