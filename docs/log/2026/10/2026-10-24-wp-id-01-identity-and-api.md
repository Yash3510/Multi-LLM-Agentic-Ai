---
title: "Identity and the API"
type: log
status: implemented
owner: R1
updated: 2026-10-24
date: 2026-10-24
branch: 4ce-core
pr: null
work_package: "WP-ID-01, WP-F-01 (server)"
author: Yash3510
areas: [core/identity, apps/server, deploy, docs]
tags: [4ce, log, identity, server, security]
---

# Identity and the API

## What changed

Backend slice 1, in small commits on `4ce-core`: sign-in, session and sign-out over an HTTP API, on SQLite or PostgreSQL.

- **`core/identity`:** users in an organisation with the seven roles, argon2id passwords (12 to 1024 characters), lockout (5 failures, 15 minutes), HS256 tokens, and revocation on sign-out. Several review fixes hardened it: failed sign-ins are counted in the database so parallel guesses can't be lost, and NUL characters, lone surrogates and over-long values are refused before the database.
- **`apps/server`:** the FastAPI app under `/api` (health, sign-in, session, sign-out, OpenAPI), cookie plus CSRF handling, one error envelope, migrations `0002` (users) and `0003` (revoked tokens) with row-level security on PostgreSQL, and the `fource-server` command (`serve`, `migrate`, `create-user`). The server and its commands use a selector event loop on Windows so psycopg's async mode can work there.
- **Tests:** a smoke test that starts the real `fource-server serve` command and signs in, on every CI system (Task 10b, `bba6c20`); a Windows fix that names the garbage-token test cases so Windows can run them (`dbb7e77`); nine PostgreSQL tests (`just test-postgres`) showing the app role can't read, write or unlock other organisations' rows.
- **Deploy and CI:** `deploy/config/postgres/10-app-role.sh` creates the `fource_app` role on a new data volume, and a CI job runs the PostgreSQL tests against a PostgreSQL 18 service. `just dev` runs the server; the bundled services moved to `just services`.
- **Docs (this entry's commits):** three new pages, [database](../../../architecture/database.md), [identity](../../../architecture/identity.md) and [API](../../../architecture/api.md), which is now the one home of the contract; the [frontend page](../../../architecture/frontend.md) points at it. The overview, indexes and [state](../../../state.md) are updated, and [ADR-0038](../../../adr/0038-signed-tokens-for-sign-in.md) records the locked-account trade-off and the missing token invalidation on password change.

## Why

Phase 0 ends with "an app with a login". The frontend owner needs a contract to code against, and every later package needs identity and an organisation-scoped database underneath it. Writing the contract once, in `api.md`, stops the frontend page and the code drifting apart. Running the same checks on PostgreSQL proves the isolation holds in the database and not only in code.

## Files

| Path | Change |
| --- | --- |
| `core/identity/` | New package: users, passwords, tokens, service, errors, roles, tests, README |
| `apps/server/src/fource/server/` | `main.py`, `deps.py`, `errors.py`, `routes/`, `cli.py`, `loops.py`, migrations `0002`, `0003` |
| `apps/server/tests/` | API, command, migration, smoke and PostgreSQL tests |
| `deploy/config/postgres/10-app-role.sh`, `.github/workflows/` | The app role on a new volume; the PostgreSQL CI job |
| `justfile`, `.env.example` | `dev`, `migrate`, `create-user`, `test-postgres`, `services`; the PostgreSQL URLs |
| `docs/architecture/database.md`, `identity.md`, `api.md` | New pages |
| `docs/architecture/frontend.md`, `overview.md`, `README.md`, `docs/README.md`, `docs/state.md` | Contract moved to `api.md`; indexes, subsystems and state updated |
| `docs/adr/0038-signed-tokens-for-sign-in.md` | Two consequences added; status unchanged (proposed) |
| `docs/log/README.md`, this entry | The log row and entry |

## How it was verified

All on the `vps` server (Debian, Python 3.12.15). The docs commits touch no code, so the code results below are for the commit before them, `6eec492`.

1. **`just check`:** exit 0. Ruff clean (135 files unchanged), pyright and import contracts clean, repo, neutrality and docs checks clean, 62 components licence-checked, gitleaks found no leaks in the history, and the tests ended with `267 passed, 9 deselected in 30.95s` (the 9 are the PostgreSQL tests). After the fresh-clone fix (item 7) `just check` exited 0 again with `268 passed, 9 deselected in 32.04s`.
2. **PostgreSQL tests:** the machine's shared PostgreSQL 17 container (`services-postgres-1`, port 5432) was stopped, the project's own PostgreSQL 18.6 started with `docker compose --env-file .env -f deploy/compose/core.yml -f deploy/compose/dev.yml up --detach --wait postgres` (healthy), then `just test-postgres`: `collected 276 items / 267 deselected / 9 selected` and `9 passed, 267 deselected in 22.91s`. The count is 9, not the 6 the plan expected. The shared container was restarted afterwards.
3. **Fresh clone on SQLite** (`git clone --branch 4ce-core` of this repository into a throwaway folder, deleted afterwards): `just setup` worked; the first `just migrate` **failed** with `sqlite3.OperationalError: unable to open database file`, because the `data/` folder does not exist on a fresh clone and the migration command did not create it. This was fixed during verification (`d9e1176` test, `8e9ee7f` fix; see item 7). After `mkdir data`: `just migrate` printed `The database is up to date.`, `create-user` printed `Created admin@example.com (Admin).`, and with `fource-server serve --port 8765`:
   - sign-in: `{"user":{"id":"01a16ce4-b1f9-779a-ae1d-7e93040c1156","email":"admin@example.com","display_name":"","roles":["Admin"],"org":"default"},"token":"<jwt>","expires_at":"2026-10-24T15:51:32.017224Z"}` (the token value is left out here)
   - session: `{"id":"01a16ce4-b1f9-779a-ae1d-7e93040c1156","email":"admin@example.com","display_name":"","roles":["Admin"],"org":"default"}`
   - sign-out with the CSRF header: `204`
   - `/api/openapi.json`: `{"openapi":"3.1.0","info":{"title":"4CE","version":"0.1.0"},"paths":{"/api/health":{"get":{"tags":["health"],"summary":"Health","operationId":"health_api_health_get","responses":{"200":{"description":`
4. **The same on PostgreSQL** (the project's PostgreSQL 18.6 with the shared container paused, URLs appended to the local `.env` and removed afterwards, `grep -c '^FOURCE_DATABASE_' .env` returned 0 before and after): `just migrate` printed `The database is up to date.`, `create-user` printed `Created admin@example.com (Admin).`, and the four calls gave the same result as on SQLite: the sign-in JSON with the user (`org` `default`), the session JSON, `204`, and the OpenAPI document; `/api/health` answered `{"status":"ok","database":"ok"}`. The server was stopped, `just down` run and `services-postgres-1` started again; `docker ps` showed it up.
5. **CI on GitHub:** checked after the push; no result is recorded here.
6. **The docs findings that were checked in code:** `/api/nope` and `/api/docs` answer 404 `{"detail":"Not Found"}` and `POST /api/health` answers 405 `{"detail":"Method Not Allowed"}`, outside the error envelope; invalid JSON in a body answers 422 `validation_failed` inside it.
7. **The fix:** a new test (migrating into a folder that doesn't exist) failed with `OperationalError` before the fix and passed after (`4 passed` in `test_migrate.py`). In a throwaway clone of the new HEAD, `just setup` then `just migrate` with no `mkdir data` printed `The database is up to date.`: `ls data` found no folder, then `The database is up to date.` and `data/fource.db` existed.

## Decisions

[ADR-0010](../../../adr/0010-modular-monolith-on-one-database.md), [ADR-0037](../../../adr/0037-licence-approvals-for-the-backend-stack.md) and [ADR-0038](../../../adr/0038-signed-tokens-for-sign-in.md), all still proposed. Made with the project lead: this work lands on `4ce-core` directly and is pushed after each reviewed task; PostgreSQL was run locally by pausing the machine's shared PostgreSQL container for the check.

## Docs updated

New: [database](../../../architecture/database.md), [identity](../../../architecture/identity.md), [API](../../../architecture/api.md). Changed: [frontend](../../../architecture/frontend.md) (status line, contract moved), [overview](../../../architecture/overview.md), the [architecture index](../../../architecture/README.md), the [docs index](../../../README.md), [state](../../../state.md), [ADR-0038](../../../adr/0038-signed-tokens-for-sign-in.md).

## Known limits and follow-ups

Issues aren't open yet (the GitHub project isn't set up); each item becomes one.

- **Errors outside the envelope:** Starlette's own 404 and 405 answers use `{"detail": …}`.
- **Tokens are not invalidated on a password change** (there is no password-change feature yet).
- **A locked account answers `423` before the password is checked,** which reveals that it exists.
- **PostgreSQL from a Windows host is not exercised in CI.** Production runs on Linux.
- **Code-level organisation scoping covers ORM statements only;** bulk and Core statements rely on PostgreSQL's row-level security.
- **No route guards per role yet** (WP-ID-02); `fource-server serve` has no `--forwarded-allow-ips` option.
- **CI** on Linux, Windows, macOS and the PostgreSQL job is checked after the push.
