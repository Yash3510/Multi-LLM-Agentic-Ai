---
title: "apps/web: sign-in, the session and sign-out against the server"
type: log
status: implemented
owner: R3
updated: 2026-11-17
date: 2026-11-17
branch: wp/WP-UI-06-sign-in
pr: null
work_package: WP-UI-06
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: sign-in, the session and sign-out against the server

## What changed

- **Sign-in on the server:** in a dev build, sign-in, the session and sign-out go to `apps/server` (`POST /api/auth/signin`, `GET /api/auth/session`, `POST /api/auth/signout`) through the dev server's `/api` proxy. The sign-in page, the layout's session check and the user menu are the same screens; only the data source behind them moved ([WP-UI-06, part 1](../../../architecture/frontend.md#wp-ui-06-part-1-sign-in-session-and-sign-out-against-the-server)).
- **Messages:** every refusal shows the server's own message: wrong details, the lockout, the rate limit (429) and the paused sign-in when the limit can't be checked (503). An answer without the error envelope reads "Can't reach the 4CE server. Check that it's running, then try again."
- **Sign-out:** sends the `fource_csrf` cookie's value as `X-CSRF-Token`. A 401 counts as signed out; any other failure shows an error toast and leaves the person signed in, where it used to do nothing visible.
- **Builds:** a demo build (`VITE_4CE_DEMO=1`) stays fake throughout; a dev build lays the server's session calls over the fake replay; a production build is still refused ([ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md)).
- **Session check:** the root layout hands SvelteKit's `fetch` to `currentUser`, so dev no longer warns on every route change that `load` used `window.fetch`.
- **Browser tests against a real server:** a `server` Playwright project runs `e2e/sign-in.spec.ts` on the dev server, in front of a throwaway `fource-server` that `e2e/server.ts` starts with `uv run fource-server migrate` and `serve` on a fresh SQLite database with a random secret.

## Why

The owner asked to connect the app to the backend piece by piece while the backend is being built, starting with login. Sign-in is the first screen off stand-in data.

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/server.ts` | new: the session calls on the server, and `ServerError` |
| `apps/web/src/lib/data/server.test.ts` | new: 12 tests with `fetch` stubbed |
| `apps/web/src/lib/data/source.ts`, `source.test.ts` | which build uses the server |
| `apps/web/src/lib/data/types.ts`, `index.ts` | `currentUser(fetch?)`; the module comment |
| `apps/web/src/routes/+layout.ts` | passes load's `fetch` to `currentUser` |
| `apps/web/src/lib/ui/components/AppShell.svelte` | an error toast when sign-out fails |
| `apps/web/vite.config.ts` | `/api` proxy for dev and preview, `API_TARGET` |
| `apps/web/playwright.config.ts` | the `server` project, the throwaway server and the dev server |
| `apps/web/e2e/sign-in.spec.ts`, `server.ts`, `account.ts` | new: the browser tests, the server launcher, the test accounts |
| `apps/web/README.md` | builds and the server |
| `docs/adr/0046-connect-screens-to-the-server-one-at-a-time.md`, `docs/adr/README.md` | new ADR, proposed |
| `docs/architecture/frontend.md` | WP-UI-06 part 1 in the §12 template; running the app against the server |
| `docs/architecture/web-data-contract.md`, `web-screens.md`, `design-system.md` | the session on the server; what is built of sign-in; where server errors show |
| `docs/state.md`, `docs/log/README.md`, this entry | status and index |

## How it was verified

On macOS (arm64), Node 24.21.0, uv 0.12.17, Python 3.12, in a fresh worktree after `uv sync --all-packages --locked` and `npm --prefix apps/web ci`. `just` and `pre-commit` aren't installed on this machine, so each `just check` recipe's commands were run directly, as the justfile writes them.

**Tests first:**

- `npx vitest run src/lib/data/server.test.ts src/lib/data/source.test.ts` before the code: `server.test.ts` failed (`Failed to resolve import "./server"`), and `source.test.ts` had 1 failed, 4 passed (a dev build still signed in on the fake: name `ada`, expected `Ada`). After the code: 2 files, 16 tests passed.
- `npx playwright test --project=server` before the shell change: 1 failed (no "Can't reach the 4CE server." after a sign-out request the test aborted), 1 passed (the lockout). After: 2 passed.
- The load-`fetch` test before the change: 1 failed, 11 passed. After: `npx vitest run src/lib/data` 4 files, 70 tests passed. A full `npm run e2e` before it logged 7 `window.fetch` warnings; `npx playwright test --project=server` after it logged 0.

**Every check:**

| Recipe | Commands | Result |
| --- | --- | --- |
| `lint` | `uv run ruff format --check .`, `uv run ruff check .`, `uv run pyright` | 212 files already formatted; all checks passed; 0 errors, 0 warnings |
| `imports` | `uv run lint-imports` | 13 contracts kept, 0 broken |
| `repo-check`, `neutrality` | `uv run python tools/repo_check.py`, `tools/neutrality_check.py` | exit 0, nothing reported |
| `docs` | `uv run python tools/docs_check.py --base origin/4ce-core` | exit 0 |
| `licences` | `tools/sbom.py`, `licence_gate.py build/sbom/python.cdx.json`, `import_scan.py …`, `licence_gate.py --bundle` | 67 components checked; 102 files scanned; 5 bundled services checked |
| `test` | `uv run pytest -m "not postgres and not redis"` | 712 passed, 85 deselected, 22.8 s |
| `web-lint` | `npm --prefix apps/web run lint`, `run lint:design`, `run check` | ESLint and Prettier clean; design lint clean; svelte-check 1447 files, 0 errors, 0 warnings |
| `web-test` | `npm --prefix apps/web test`, `npm --prefix apps/web exec -- vitest run --root . --dir tools` | 92 files, 563 tests passed; 3 files, 16 tests passed |
| `web-e2e` | `npm --prefix apps/web run e2e` | 10 passed in 22.2 s (desktop and tablet on the demo build, and the 2 sign-in tests on the `server` project); 0 `window.fetch` warnings |

**Not run:** `just secrets` (gitleaks through `pre-commit`, not installed here); the PostgreSQL and Redis test sets (`just test-postgres`, `just test-redis`), which this change doesn't touch; CI, which runs on pull requests, and none is open.

## Decisions

- [ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md), proposed: screens move to the server one call at a time; demo builds stay fake, production builds wait; hand-written shapes until WP-UI-05, a departure from ADR-0035 §4; server-backed browser tests on the dev server.
- The browser test adds its accounts in Python, as `apps/server/tests/test_smoke.py` does, not with `fource-server create-user`: that command reads the password with `getpass`, which reads the console rather than a pipe on Windows (and `/dev/tty` where one exists), so a test would hang there.
- `currentUser` treats an unreachable server as signed out, so the person lands on the sign-in page, where signing in says the server is out of reach.
- No new dependency.

## Docs updated

[Frontend](../../../architecture/frontend.md), [web data contract](../../../architecture/web-data-contract.md), [web screens](../../../architecture/web-screens.md), [design system](../../../architecture/design-system.md), [ADR-0046](../../../adr/0046-connect-screens-to-the-server-one-at-a-time.md) and the ADR index, the [web README](../../../../apps/web/README.md), [state](../../../state.md) and the [work log index](../../README.md).

## Known limits and follow-ups

No issues are open for these yet: the repository is public, and they wait for the owner's word.

- **Roles:** only Admin maps to the web app's `admin`; the other six roles show as `user` until route guards per role (WP-ID-02).
- **Stand-in screens** still name the stand-in account where they show an owner.
- **The rest of WP-UI-06:** no return path after signing in, no session-expiry banner, no no-access or error pages.
- **Languages:** the server's messages are English, also in the Hindi locale.
- **Windows:** the launcher runs without a shell and adds accounts without a console prompt, written for Windows but checked only on macOS here; CI runs it on all three systems once a pull request is open.
- **Temporary folders:** each run of the sign-in browser tests leaves a small `4ce-e2e-*` folder, holding its SQLite file, in the system's temporary directory, for the system to clear.
- **Formatting:** `docs/architecture/design-system.md` already fails Prettier on `4ce-core`; the docs aren't under Prettier's check, and this change leaves that as it was.
