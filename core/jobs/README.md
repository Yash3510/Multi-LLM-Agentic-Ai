# fource-jobs

The job queue (master plan §6.3): work queued in the database in the same transaction as the state that needs it, and the worker loop that takes and runs it. Every job belongs to one organisation, under row-level security.

**Owner:** R1 · **Decisions:** [ADR-0040](../../docs/adr/0040-job-queue-on-postgresql.md)

## Public API

| Name | What it is |
| --- | --- |
| `Job`, `JobState`, `UNFINISHED` | The `jobs` table and its four states (`queued`, `running`, `done`, `failed`); at most one unfinished job per organisation and key |
| `enqueue(session, kind, payload=None, *, run_at=None, key=None, max_attempts=5)` | Queues a job of the session's organisation in the session's transaction, so it commits with the state that needs it. `kind` is lower-case dotted (`ledger.checkpoint`); `payload` a JSON object of at most 16 KiB holding ids and small parameters, never content or secrets; `run_at` must carry a time zone; with `key`, a job of that key still queued or running is returned instead of a second one. On PostgreSQL the commit wakes listening workers (`pg_notify` on `fource_jobs`) |
| `take(session, kinds, *, lease)`, `HeldJob` | Takes the organisation's oldest due job of those kinds, or a running one whose lease ran out, and holds it for `lease` under a fresh `holder` token (`kinds` is a non-empty collection, never a bare string; `lease` is positive); commit at once. PostgreSQL skips rows other takers hold (`FOR UPDATE SKIP LOCKED`); SQLite has no row locks, and its write lock lets one taker in at a time |
| `complete(session, job)`, `LeaseLost` | Marks the job done in the transaction its handler wrote in, so the work and the completion commit together. Only the current holder can: if another worker has taken the job since, it raises `LeaseLost` and the caller's rollback undoes the attempt |
| `retry_or_fail(session, job, error)`, `backoff(attempts)`, `describe(error)`, `Unfinished` | Records a failed attempt in a transaction of its own: queued again after 30 s, doubling to an hour, or `failed` after `max_attempts`; like `complete`, it raises `LeaseLost` if another worker holds the job now. Only a `FourceError`'s message or the error's class name is kept (`describe`), never other text, which could quote documents or URLs |
| `Worker(database, handlers, *, recurring=(), poll_seconds=2.0)`, `Handler(run, lease=)`, `Recurring(kind, every)` (a lease or interval of zero or less, or a poll that is not a positive finite number, raises `ValueError`) | The worker loop. `run_once()` keeps each recurring job queued in every organisation (key `recurring:<kind>`, due one interval after the last one finished, queued at most once per interval even with several workers; this assumes the workers' clocks are synced, because the at-most-once re-check compares `finished_at` times), then runs due jobs, one organisation session at a time, until none is left (an organisation whose step raises is logged once per pass with its id and the error's class name and the others go on; if it was a job round, that organisation is skipped for the rest of the pass, but a failure keeping recurring jobs queued leaves its ordinary jobs alone); `run()` repeats that until `stop()`, waiting for `wake()` or the poll in between. A handler's writes commit with the job's completion; a failure is retried after backoff; a job whose last attempt never finished fails without running again |
| `listen_for_jobs(url, on_wake, stop, *, retry_seconds=5.0)` | PostgreSQL only: LISTENs on `fource_jobs` on a connection of its own and calls `on_wake` for each NOTIFY (and once when it starts), reconnecting after a drop or any other error (logged by class name only; connecting times out after 10 s); `Worker.run()` starts it. SQLite has no notifications, so there the worker only polls |

## Tests

```
uv run pytest core/jobs
```
