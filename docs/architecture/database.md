---
title: Database
type: architecture
status: active
owner: R1
updated: 2026-10-25
covers:
  - core/db/
  - apps/server/src/fource/server/migrations/
tags: [4ce, architecture, security, deploy]
---

# Database

How 4CE stores its rows, keeps one organisation's rows away from another's, and changes the schema. The code is [`core/db`](../../core/db/README.md) and the migrations in `apps/server`.

## Engines

- **SQLite** is the default (`sqlite+aiosqlite:///data/fource.db`), so the server runs with no setup. It needs SQLite 3.35 or newer, because the lockout counter uses `UPDATE … RETURNING`.
- **PostgreSQL** (18, see [services](services.md)) is the production engine. Set `FOURCE_DATABASE_URL` to a `postgresql+psycopg://` URL; [`.env.example`](../../.env.example) shows the form.
- **Two URLs on PostgreSQL.** The server connects as `fource_app` (`FOURCE_DATABASE_URL`). Migrations run as the owner role (`FOURCE_DATABASE_ADMIN_URL`); without it, they use the one URL.
- `Database` (in `fource.db`) wraps one async engine. On SQLite it creates the folder, and turns foreign keys on for every connection.

## Organisation sessions

`Database.org_session(org_id)` gives a session confined to one organisation, and commits on success. `Database.session()` is unscoped and for the `orgs` table and set-up only. `org_of(session)` returns the organisation an organisation session is confined to (and raises for any other session); the [ledger](ledger.md) uses it to find whose chain to extend. Three rules apply in code to every table that inherits `OrgScoped`:

1. **Reads are filtered** to the organisation (ORM selects, updates and deletes get the criterion added).
2. **New rows are stamped** with the organisation.
3. **Cross-organisation writes are refused** with `CrossOrgWrite` (403, `cross_org_write`): inserting, changing or deleting a row of another organisation, including one whose `org_id` was changed before the flush.

**What the code guard does not cover.** It works on ORM flushes and ORM statements. Bulk or Core statements (`update()` and `insert()` built on a `Table`) and selects on `Table` objects are not scoped by it. PostgreSQL's row-level security is the backstop there.

## Row-level security

On PostgreSQL the same organisation is also enforced by the database:

- Each organisation session sets `fource.org_id` for its transaction (`set_config(…, true)`).
- `org_isolation_sql(table)` returns the statements a migration runs: `ENABLE` and `FORCE ROW LEVEL SECURITY` (FORCE applies the policy to the table's owner too), a policy named `org_isolation` whose `USING` and `WITH CHECK` are `org_id = NULLIF(current_setting('fource.org_id', true), '')::uuid`, and a grant of `SELECT, INSERT, UPDATE, DELETE` to the app role. An unset setting matches no rows. `org_isolation_sql(table, privileges=…)` grants fewer privileges to a table the app role must not change: the ledger grants `SELECT, INSERT` on `ledger_entries` and `SELECT, INSERT, UPDATE` on `ledger_heads` ([ledger](ledger.md#insert-only)). The function refuses any name that is not a plain lower-case identifier, and any privilege outside those four.
- **`fource_app`** (`APP_ROLE`) is `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS`. [`deploy/config/postgres/10-app-role.sh`](../../deploy/config/postgres/10-app-role.sh) creates it, with `FOURCE_POSTGRES_APP_PASSWORD`, when PostgreSQL first creates its data volume. On an existing volume it does not run: create the role by hand.
- **The owner role** (`fource`, `FOURCE_POSTGRES_PASSWORD`) owns the tables and runs migrations. The server must not connect as it or as any superuser or `BYPASSRLS` role, which would bypass the policy: on PostgreSQL it checks its own role at start-up and refuses to start (`UnsafeDatabaseRole`, a message naming the role and saying to connect as `fource_app` through `FOURCE_DATABASE_URL`). The check connects, so an unreachable database fails start-up too; SQLite has no roles and is not checked.
- `orgs` has no policy: the app role may only read it.

## Migrations

- **Where:** `apps/server/src/fource/server/migrations/versions/`, one Alembic history for every package's tables, named `NNNN_what_it_does.py` (`0001` to `0004` today: organisations, users, revoked tokens, the [ledger](ledger.md) with its insert-only triggers).
- **Batch mode** is on (`render_as_batch`), so SQLite can alter tables.
- **Dialect branches:** a migration runs the row-level security and grant statements only when the connection is PostgreSQL.
- **Downgrades** exist for every revision (`fource.server.migrate.downgrade`), used by tests; production upgrades are forward-only.
- **Running them:** `just migrate` (`fource-server migrate`) upgrades to the head. `just dev` migrates first. The migration environment uses the same event loop rules as the server ([API](api.md#running-it)).
- A new model must be imported in `migrations/env.py` so its table reaches the metadata.

## What needs PostgreSQL

The SQLite suite (`just test`) cannot show row-level security, so the tests marked `postgres` run only against PostgreSQL: the app role cannot read, write or unlock another organisation's rows, and the paths that differ by engine (NUL and over-long values, `UPDATE … RETURNING`). On PostgreSQL they also cover the ledger (the app role can only add and read entries, not even the owner can change or empty them, concurrent writers keep the chain whole) and the start-up refusal of a role that bypasses row-level security. Run them with `just services`, `just test-postgres`, `just down`. CI runs them against a PostgreSQL 18 service in its own job.

## Known limits

- **Windows and PostgreSQL.** psycopg's async mode doesn't run on Windows' default event loop. The server and its commands use a selector event loop so it can work, but PostgreSQL from a Windows host is not exercised in CI (unverified). Production runs on Linux.
- Bulk and Core statements are not scoped in code (above).
- **A SQLite batch rebuild of `ledger_entries` must recreate its insert-only triggers** (`ledger_entries_no_update`, `ledger_entries_no_delete`); a migration that rebuilds the table otherwise drops them silently.

## Decisions

[ADR-0010](../adr/0010-modular-monolith-on-one-database.md) (one database, isolation in both layers), [ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md) (the ledger's insert-only tables). Licences of the drivers: [ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md). The services themselves: [services](services.md).
