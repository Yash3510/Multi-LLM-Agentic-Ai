# fource-server

The 4CE server: the API routes, the `fource-server` command and the one Alembic history for every package's tables ([ADR-0010](../../docs/adr/0010-modular-monolith-on-one-database.md)).

**Owner:** R1

## Migrations

- They live in `src/fource/server/migrations/versions/`, named `NNNN_what_it_does.py`, revision ids `"NNNN"`.
- They run on SQLite and PostgreSQL (batch mode). On PostgreSQL every organisation's table gets `fource.db.org_isolation_sql(table)`.
- Each one has a downgrade, and `tests/test_migrate.py` runs up, down and up again.
- The ledger (`0004`) grants the app role less: `org_isolation_sql(table, privileges=…)`, and adds insert-only triggers on both engines. A migration that rebuilds `ledger_entries` on SQLite (batch mode) must recreate its triggers.

## Running it

```
just dev                                    # migrate, then run on http://127.0.0.1:8000 with live reload
just migrate                                # bring the database schema up to date
just create-user you@example.com --role Admin   # asks for the password twice
just ledger keygen       # once: the installation's signing key, in data/ledger/ (never committed)
just ledger checkpoint   # sign the chain head; keep the file it writes somewhere off this machine
just ledger verify       # check the chain; exit 0 verified, 1 problems, 2 not everything checked
```

The smoke test (`tests/test_smoke.py`) starts the real `fource-server` command on a throwaway SQLite database, so CI proves it runs on Linux, Windows and macOS.

On Windows the server and its commands use a selector event loop, because psycopg's async mode needs one.

## Database role

On PostgreSQL the server refuses to start if its role is a superuser or has `BYPASSRLS`, because either would switch off the isolation between organisations. Connect it as `fource_app` through `FOURCE_DATABASE_URL`; `FOURCE_DATABASE_ADMIN_URL` (the owner) is for `migrate` only.

## Tests

```
uv run pytest apps/server
```
