# fource-jobs

The job queue (master plan §6.3): work queued in the database in the same transaction as the state that needs it, and the worker loop that takes and runs it. Every job belongs to one organisation, under row-level security.

**Owner:** R1 · **Decisions:** [ADR-0040](../../docs/adr/0040-job-queue-on-postgresql.md)

## Public API

| Name | What it is |
| --- | --- |
| `Job`, `JobState`, `UNFINISHED` | The `jobs` table and its four states (`queued`, `running`, `done`, `failed`); at most one unfinished job per organisation and key |
| `enqueue(session, kind, payload=None, *, run_at=None, key=None, max_attempts=5)` | Queues a job of the session's organisation in the session's transaction, so it commits with the state that needs it. `kind` is lower-case dotted (`ledger.checkpoint`); `payload` a JSON object of at most 16 KiB holding ids and small parameters, never content or secrets; with `key`, a job of that key still queued or running is returned instead of a second one. On PostgreSQL the commit wakes listening workers (`pg_notify` on `fource_jobs`) |
| `take(session, kinds, *, lease)`, `HeldJob` | Takes the organisation's oldest due job of those kinds, or a running one whose lease ran out, and holds it for `lease` under a fresh `holder` token; commit at once. PostgreSQL skips rows other takers hold (`FOR UPDATE SKIP LOCKED`); SQLite has no row locks, and its write lock lets one taker in at a time |

## Tests

```
uv run pytest core/jobs
```
