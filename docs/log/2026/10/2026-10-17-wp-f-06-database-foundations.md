---
title: "Database foundations"
type: log
status: implemented
owner: R1
updated: 2026-10-17
date: 2026-10-17
branch: 4ce-core
pr: null
work_package: WP-F-06
author: Yash3510
areas: [core/common, core/db, apps/server, tools]
tags: [4ce, log, common, security, licences]
---

# Database foundations

## What changed

The database foundations of the backend, in small commits on `4ce-core` (a test commit first, then the code):

- **`core/common`:** time-ordered ids (`new_id`, in creation order even within a millisecond), a replaceable clock (`now`, `set_clock`) and the base error `FourceError` with a code and an HTTP status.
- **Settings:** `Settings` now needs only `FOURCE_SECRET_KEY` (at least 32 characters). `FOURCE_DATABASE_URL` defaults to SQLite, so the server starts with no setup; `FOURCE_DATABASE_ADMIN_URL`, `FOURCE_ORG` and `FOURCE_TOKEN_TTL_MINUTES` are new, and Redis and S3 settings became optional. A rejected secret key is never printed in the error. `just setup` creates `.env` with fresh secrets (`tools/dev/env.py`), and `data/` is ignored.
- **Licence approvals by ADR:** the licence gate passes a review-required licence for a package an ADR approved, listed under `[[approved]]` with its exact licence ([ADR-0037](../../../adr/0037-licence-approvals-for-the-backend-stack.md): psycopg, psycopg-binary, certifi, cffi). A changed licence lapses the approval.
- **`core/db` ([ADR-0010](../../../adr/0010-modular-monolith-on-one-database.md)):** `Database` (async engine for SQLite or PostgreSQL), organisation-scoped sessions that filter reads to one organisation, stamp new rows with it and refuse cross-organisation inserts, edits and deletes (`CrossOrgWrite`), the `Base`, `OrgScoped` and `Org` models, and `UtcDateTime`, which refuses a time without a zone.
- **Row-level security SQL:** `APP_ROLE` (`fource_app`) and `org_isolation_sql(table)`, which returns the statements a migration runs to put a table under row-level security. It refuses any table name that is not a plain lower-case identifier, and reads the session setting safely when it is unset.
- **`apps/server`:** the package, with the one Alembic history for every package's tables. Migration `0001` creates `orgs` and the `default` organisation, and on PostgreSQL grants the app role read access. `fource.server.migrate` has `alembic_config`, `upgrade`, `downgrade` and `migration_url` (migrations use `FOURCE_DATABASE_ADMIN_URL` when it is set). A `%` in a database URL reaches Alembic intact. The workspace now includes `apps/*`, pyright is strict for `apps/`, pytest runs with `--strict-markers` and a `postgres` marker, and a layers contract puts `fource.server` above `fource.db` above `fource.common`.

## Why

Every later package (identity, the job queue, the ledger, the domain model) stores its rows in one database, so the rules for who may read and write a row have to exist before the first table does. Doing it in the session and again in PostgreSQL's row-level security means a mistake in one layer is caught by the other. Migrations run on SQLite and PostgreSQL from one history, so a new contributor can run everything with no database server.

## Files

| Path | Change |
| --- | --- |
| `core/common/src/fource/common/` | New `ids.py`, `clock.py`, `errors.py`; `settings.py` and `__init__.py` changed |
| `core/common/tests/`, `core/common/README.md` | New id, clock and error tests; settings tests rewritten; API table updated |
| `core/db/` | New package: `types.py`, `models.py`, `database.py`, `isolation.py`, tests, README |
| `apps/server/` | New package: `pyproject.toml`, README, `migrate.py`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_create_orgs.py`, tests |
| `pyproject.toml`, `uv.lock` | Workspace members, pyright, pytest options and marker, the `fource.db` and layers import contracts |
| `tools/dev/env.py`, `tools/tests/test_env.py`, `justfile`, `.env.example`, `.gitignore` | `.env` created by `just setup` |
| `tools/licence_gate.py`, `tools/licence-review.toml`, `tools/tests/test_licence_gate.py` | ADR approvals; `uvloop` recorded as `MIT OR Apache-2.0` |
| `docs/adr/0010-modular-monolith-on-one-database.md`, `docs/adr/0037-licence-approvals-for-the-backend-stack.md`, `docs/adr/README.md` | New ADRs, both proposed |
| `docs/architecture/licences.md`, `docs/architecture/repository.md` | Updated for the approvals, `uvloop`, `apps/server` and the new contract |

## How it was verified

All on the Debian laptop, Python 3.12.15, uv 0.13.0. Each task wrote its tests first and saw them fail for the right reason before the code was written.

- **`core/common`:** RED was `ImportError: cannot import name 'new_id' from 'fource.common'` (and the same for `FourceError`). Then `uv run pytest core/common -q -W error` gave 13 passed. Breaking the same-millisecond counter made `test_ids_made_in_a_row_are_already_in_order` fail (1 failed, 3 passed); the line was restored.
- **Settings and `.env`:** RED was 4 failed, 2 passed for the settings tests, and 1 failed, 4 passed for `tools/tests/test_env.py`. GREEN: `uv run pytest core/common tools -q` gave 115 passed. A later test shows a rejected key is not printed in the error (RED 1 failed, 6 passed; GREEN 7 passed).
- **Licence gate:** RED was `AttributeError: module 'licence_gate' has no attribute 'load_approved'` (3 failed, 11 passed). GREEN: `uv run pytest tools -q` gave 103 passed, and the gate checked 30 components. Removing the licence-equals-approval test, and matching any package name, each failed a test.
- **`core/db`:** `uv run pytest core/db -q -W error` gave 9 passed first, then 15 after the review fixes (cross-organisation deletes, a time without a zone, the organisation a row was loaded with). Disabling the read filter failed 4 tests and disabling the cross-organisation refusal failed 1.
- **Row-level security SQL:** `uv run pytest core/db -W error -q` gave 21 passed. Disabling the identifier guard failed 4 tests (all four bad names), and removing `NULLIF` from the policy failed the unset-setting test.
- **`apps/server`:**
  - RED: `uv run pytest apps/server -q` gave `ModuleNotFoundError: No module named 'fource.server.migrate'`.
  - GREEN: `uv run pytest apps/server -W error -q` gave 3 passed. The tests run `upgrade`, `downgrade` to `base` and `upgrade` again on a temporary SQLite file and check the `default` organisation row, check that `%25` in a URL survives, and check `migration_url` prefers the admin URL.
  - Removing `.replace("%", "%%")` from `alembic_config` made the `%` test fail with `ValueError: invalid interpolation syntax`; the line was restored.
  - `uv run pyright`: 0 errors, 0 warnings. `uv run lint-imports`: 5 contracts kept, 0 broken.
  - `just licences`: stopped first on `uvloop` 0.23.0 ("Apache Software License" is not a licence the policy names). Its LICENSE-MIT and LICENSE-APACHE files were read and it was recorded as `MIT OR Apache-2.0`; then 52 components checked, 27 files scanned, 5 bundled services complete.
- **Whole repository after `apps/server`:** `uv run pytest -q` gave 158 passed (`core/common` 15, `core/db` 21, `core/packs` 16, `apps/server` 3, `tools` 103).
- **`just check`** at the end of this work (exit 0): ruff clean, pyright 0 errors, 5 import contracts kept, repo, neutrality and docs checks clean, 52 components licence-checked and 27 files import-scanned, 5 bundled services complete, gitleaks found no leaks in the branch's history, 158 tests passed.

## Decisions

Proposed: [ADR-0010](../../../adr/0010-modular-monolith-on-one-database.md) (one modular monolith on one database, with the isolation in both the session and PostgreSQL) and [ADR-0037](../../../adr/0037-licence-approvals-for-the-backend-stack.md) (licence approvals for psycopg, psycopg-binary, certifi and cffi). R4 confirms the second.

Made with the project lead: this work lands on `4ce-core` directly and is pushed after each reviewed task, instead of one branch and pull request per task.

## Docs updated

[Licences](../../../architecture/licences.md) (approvals by ADR, `uvloop`), [repository layout](../../../architecture/repository.md) (`apps/server`, `core/db`, the layers contract, strict types for `apps/`), the [ADR index](../../../adr/README.md), and the READMEs of [`core/common`](../../../../core/common/README.md), [`core/db`](../../../../core/db/README.md) and [`apps/server`](../../../../apps/server/README.md). [State](../../../state.md) is not changed yet: it is updated when the login API works.

## Known limits and follow-ups

Issues aren't open yet (the GitHub project isn't set up); each item becomes one.

- **PostgreSQL is not exercised yet.** The `fource_app` role is created with the PostgreSQL test setup, which comes later in this slice, so the PostgreSQL branch of migration `0001` (the `GRANT`) and the row-level security statements run only then (tests marked `postgres`).
- **`fource-server` has no command yet.** `[project.scripts]` names `fource.server.cli:main`; the module is added with the command line.
- **Routes, sign-in and the identity tables** are next (WP-ID-01); their migrations extend this history from `0002`.
