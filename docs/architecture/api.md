---
title: API
type: architecture
status: active
owner: R1
updated: 2026-10-25
covers:
  - apps/server/src/fource/server/
tags: [4ce, architecture, server, security]
---

# API

The canonical contract between the 4CE server and its clients, the web UI first. The machine-readable form is the OpenAPI document at `GET /api/openapi.json`; this page says what the document can't. If the two disagree with the code, the code is the truth. The server is [`apps/server`](../../apps/server/README.md).

**One origin.** The UI and the API are served from the same host, and every API path starts with `/api`. The Swagger and ReDoc pages are off (they load assets from a CDN, and 4CE runs offline), so `/api/docs` does not exist.

## Endpoints

| Method and path | Needs | Body or answer |
| --- | --- | --- |
| `GET /api/health` | nothing | `{"status": "ok", "database": "ok"}`; 503 when the database is down |
| `POST /api/auth/signin` | nothing | sends `{"email", "password"}`; answers `{"user", "token", "expires_at"}` and sets two cookies |
| `GET /api/auth/session` | signed in | `{"id", "email", "display_name", "roles", "org"}` |
| `POST /api/auth/signout` | signed in, plus the CSRF header | ends the sign-in and clears the cookies |
| `GET /api/openapi.json` | nothing | the full contract |

Details the table leaves out:

- **Health** answers `{"status": "unavailable", "database": "unavailable"}` with 503 when the database can't be reached.
- **Sign-in** takes `email` (3 to 320 characters) and `password` (1 to 1024). It answers 200 with `user` (`id`, `email`, `display_name`, `roles`, `org`), `token` (the same value as the cookie, for scripts) and `expires_at` (UTC). The `org` is the organisation's slug, `FOURCE_ORG`.
- **Sign-out** answers `204` with no body. A second sign-out with the same token answers 401 `not_authenticated`, like any call with a revoked token (`test_signing_out_by_bearer_needs_no_csrf_and_revokes` pins this for the session call, `test_a_second_sign_out_with_the_same_credentials_is_not_authenticated` for sign-out).

## Cookies and CSRF

- **`fource_token`** is HttpOnly and SameSite=Strict, path `/`. The browser sends it automatically; JavaScript never sees it. **Ignore the `token` in the sign-in answer in a browser;** it is for scripts.
- **`fource_csrf`** is readable by JavaScript and SameSite=Strict, path `/`. A new random value is set at each sign-in.
- Both last as long as the token (`FOURCE_TOKEN_TTL_MINUTES`, 480 minutes by default), and both get the `Secure` flag when the request arrived over HTTPS.
- **The CSRF header:** every POST, PUT, PATCH or DELETE authenticated by the cookie must send the `fource_csrf` cookie's value as `X-CSRF-Token`, or the server answers 403 `csrf_failed`. Read it with `document.cookie` for each request. GET, HEAD and OPTIONS need no header.
- **Scripts** can send `Authorization: Bearer <token>` instead of cookies; that needs no CSRF header, and when it is present the cookies are ignored.
- **Signing in again replaces both cookies.** Signing out revokes the token on the server and clears both cookies. After the lifetime ends, any call answers 401 `not_authenticated`: send the person to the sign-in screen. How tokens work: [identity](identity.md#tokens).
- **Behind a TLS proxy,** the server sees plain HTTP and would leave `Secure` off. Run Uvicorn with `--forwarded-allow-ips` set to the proxy's address, so it trusts `X-Forwarded-Proto` (`fource-server serve` has no such option yet; start Uvicorn directly, see [Running it](#running-it)).

## Errors

Every error the application raises has the same shape:

```json
{ "error": { "code": "invalid_credentials", "message": "The email or password is wrong." } }
```

| Code | Status | Show the person |
| --- | --- | --- |
| `invalid_credentials` | 401 | the message; the email is kept, the password field cleared |
| `account_locked` | 423 | the message (locked for 15 minutes after 5 failed attempts) |
| `not_authenticated` | 401 | the sign-in screen |
| `csrf_failed` | 403 | a reload prompt; it means the cookie and header disagree |
| `validation_failed` | 422 | the message next to the form |
| `weak_password` | 422 | the message (a password needs 12 to 1024 characters); raised when a password is set, not by the endpoints today |
| `invalid_email` | 422 | the message; raised when a user is created, not by the endpoints today |
| `email_taken` | 409 | the message; raised when a user is created, not by the endpoints today |
| `cross_org_write` | 403 | a generic failure; a bug or an attack, never a normal path |
| `setup_incomplete` | 503 | "the server isn't set up", for an administrator: the database has no migrations yet (`just migrate`) |
| `not_found` | 404 | the not-found screen; no such path |
| `method_not_allowed` | 405 | a generic failure; a bug in the client |
| `http_error` | other | a generic failure; any other status Starlette raises itself |
| `internal_error` | 500 | a generic failure; the message says nothing about the cause, and the server logs it |

Use `code` for logic and `message` for display. A code is never renamed; a new one may be added.

Starlette's own answers use the same envelope: an unknown path (including `/api/docs`) is 404 `not_found`, a wrong method is 405 `method_not_allowed` (with its `Allow` header), and any other status Starlette raises itself gets the generic code `http_error`. A request body that isn't valid JSON is `validation_failed`, 422. The OpenAPI document declares this envelope (`ErrorOut`) for the error statuses of each auth route, in place of FastAPI's default 422 `HTTPValidationError`.

## Running it

```
just setup                                     # once: Python, packages, git hooks, a .env with fresh secrets
just dev                                       # migrate, then serve on http://127.0.0.1:8000 with reload; SQLite, no Docker
just create-user you@example.com --role Admin  # once: asks for a password twice
just ledger keygen                             # once: the installation's signing key
```

The `fource-server` command (`uv run fource-server …`):

| Command | What it does |
| --- | --- |
| `serve [--host 127.0.0.1] [--port 8000] [--reload]` | runs the API with Uvicorn |
| `migrate` | brings the database schema up to date (as the admin URL when set) |
| `create-user EMAIL --role ROLE [--role …] [--name NAME]` | adds a user in `FOURCE_ORG`; `ROLE` is one of the seven [roles](identity.md#users-and-roles); asks for the password twice, with no echo (it reads stdin when it is not a terminal) |
| `ledger keygen` | creates the installation's Ed25519 signing key and its public key; never overwrites either (exit 1 if one exists) |
| `ledger checkpoint [--org SLUG] [--out DIR]` | signs the head of the organisation's ledger chain (default `FOURCE_ORG`), records it as the next entry, prints it and saves it to `<FOURCE_DATA_DIR>/ledger/checkpoints/` (`FOURCE_DATA_DIR` defaults to `data`) or `DIR`; exit 1 if there is no key, no organisation, no entries, or the file already exists (the entry is then still recorded; keep the printed JSON) |
| `ledger verify [--org SLUG] [--public-key FILE] [--checkpoints DIR]` | checks the chain and the checkpoint files; exit 0 verified, 1 problems or an unusable path or file, 2 nothing wrong found but signatures unchecked (no public key). A zero exit may still say the chain's length is not proven. See [ledger](ledger.md#verifying) |

- **Settings** come from the environment and `.env`: `FOURCE_SECRET_KEY` (required, 32 characters or more), `FOURCE_DATABASE_URL`, `FOURCE_DATABASE_ADMIN_URL`, `FOURCE_TOKEN_TTL_MINUTES`, `FOURCE_ORG` and `FOURCE_LEDGER_KEY_FILE` (the ledger signing key, default `<FOURCE_DATA_DIR>/ledger/signing-key.pem`, `data/…` unless `FOURCE_DATA_DIR` is set). See [database](database.md) for the PostgreSQL form.
- **Migrate before the first sign-in.** Without it (no organisation row, or no tables at all), sign-in answers `setup_incomplete`. The session and sign-out calls need a valid token, which only a sign-in on a set-up database issues, so they can't reach an unmigrated database.
- **Start-up on PostgreSQL.** `serve` connects to the database before it answers, to check its role, and refuses to start (`UnsafeDatabaseRole`) if the role is a superuser or has `BYPASSRLS`; connect as `fource_app` through `FOURCE_DATABASE_URL` ([database](database.md#row-level-security)). An unreachable database therefore fails start-up, where it used to start and answer `/api/health` with 503. SQLite is not checked.
- **Event loop.** On Windows the server and its commands use a selector event loop, because psycopg's async mode can't use the default one. Linux and macOS use the default.
- **Behind a proxy,** start Uvicorn directly: `uvicorn --factory fource.server.main:app_factory --forwarded-allow-ips <proxy address>`.
- **Using the API as a script:** sign in, keep the cookies, send the CSRF header.

```
curl -c jar -X POST localhost:8000/api/auth/signin -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"…"}'
curl -b jar localhost:8000/api/auth/session
curl -b jar -X POST localhost:8000/api/auth/signout \
  -H "X-CSRF-Token: $(awk '$6=="fource_csrf"{print $7}' jar)"
```

## Decisions

[ADR-0038](../adr/0038-signed-tokens-for-sign-in.md) (tokens, cookies, CSRF, revocation), [ADR-0035](../adr/0035-frontend-foundations.md) (one origin, generated types), [ADR-0014](../adr/0014-ledger-with-signed-checkpoints.md) (the ledger commands). The frontend side of the agreement: [frontend](frontend.md).
