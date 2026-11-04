# fource-db

Database engines, sessions and organisation scoping for every 4CE package. SQLite is the zero-setup default; PostgreSQL 18 is the production database.

**Owner:** R1 · **Decisions:** [ADR-0010](../../docs/adr/0010-modular-monolith-on-one-database.md)

## Public API

| Name | What it is |
| --- | --- |
| `Database(url)` | An async engine for SQLite (`sqlite+aiosqlite://…`, creating the file's folder) or PostgreSQL (`postgresql+psycopg://…`) |
| `Database.org_session(org_id)` | The session for one organisation: reads are filtered to it, new rows take it, writes into another raise `CrossOrgWrite`; on PostgreSQL it also sets `fource.org_id` for row-level security. Commits on success, rolls back on error. |
| `Database.session()` | Unscoped; only for `orgs` and set-up work |
| `Database.org_id(slug)`, `org_slug(id)`, `ping()`, `dispose()` | Helpers |
| `Base`, `OrgScoped`, `Org` | The declarative base, the mixin every organisation's table uses (`id`, `org_id`, `created_at`), and the organisations table |
| `UtcDateTime` | A timestamp stored in UTC and read back aware on both engines |
| `CrossOrgWrite` | The error for writing into another organisation |
| `APP_ROLE`, `org_isolation_sql(table, privileges=…)` | The role the server connects as on PostgreSQL, and the statements a migration runs to put a table under row-level security; `privileges` (default all four of `SELECT`, `INSERT`, `UPDATE`, `DELETE`) lets a table such as the ledger grant the app role less |
| `table_missing(error)` | Whether a database error means a table doesn't exist yet (not migrated): SQLite's "no such table" or PostgreSQL state 42P01. Any other error is not |
| `org_of(session)` | The organisation an organisation session belongs to; `RuntimeError` for any other session, so code that must run inside one (a ledger write) can't run outside it |

## Tests

```
uv run pytest core/db
```
