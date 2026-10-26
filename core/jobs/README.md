# fource-jobs

The job queue (master plan §6.3): work queued in the database in the same transaction as the state that needs it, and the worker loop that takes and runs it. Every job belongs to one organisation, under row-level security.

**Owner:** R1 · **Decisions:** [ADR-0040](../../docs/adr/0040-job-queue-on-postgresql.md)

## Public API

| Name | What it is |
| --- | --- |
| `Job`, `JobState`, `UNFINISHED` | The `jobs` table and its four states (`queued`, `running`, `done`, `failed`); at most one unfinished job per organisation and key |

## Tests

```
uv run pytest core/jobs
```
