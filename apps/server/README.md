# fource-server

The 4CE server: the API routes, the `fource-server` command and the one Alembic history for every package's tables ([ADR-0010](../../docs/adr/0010-modular-monolith-on-one-database.md)).

**Owner:** R1

## Migrations

- They live in `src/fource/server/migrations/versions/`, named `NNNN_what_it_does.py`, revision ids `"NNNN"`.
- They run on SQLite and PostgreSQL (batch mode). On PostgreSQL every organisation's table gets `fource.db.org_isolation_sql(table)`.
- Each one has a downgrade, and `tests/test_migrate.py` runs up, down and up again.

## Tests

```
uv run pytest apps/server
```
