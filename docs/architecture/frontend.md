---
title: Frontend
type: architecture
status: planned
owner: R3
updated: 2026-11-17
covers:
  - apps/web/
tags: [4ce, architecture, frontend]
---

# Frontend

Everything needed to build `apps/web`, the 4CE web UI and Pack Studio, independently of the backend work. **Pranay, the frontend owner, develops it.** The backend stream builds the server and the database on `4ce-core` at the same time. The two meet at one contract: the server's OpenAPI document.

The web UI is not built yet; the backend contract below is. This page is the starting point and the working agreement.

## What is already decided

| Record                                                         | Decides                                                                                                                                                                                                                                        | Status                                                                             |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| [ADR-0035](../adr/0035-frontend-foundations.md)                | Stack and exact versions, static serving from the server, live updates, the fake API until the backend lands, roles and labels, devices, languages, theme, accessibility, no glass, icons, quality gates, clean room                           | proposed; accepted by the frontend owner; R1 to accept §2 (serving) and §5 (roles) |
| [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) | How the licence gate treats MPL-2.0 build and test tools (lightningcss, axe-core) and permissive licences Appendix A doesn't name                                                                                                              | proposed; R4 to accept before `apps/web` lands on `4ce-core`                       |
| [ADR-0041](../adr/0041-exact-match-look.md)                    | The look matches the running 4CE app, measured; its amendment sets premium base components (the running app's Phosphor icons, hairline depth, soft focus glow). Supersedes ADR-0035's theme, colour values, no-glass rule and design-lint part | proposed; accepted by the frontend owner; R1 to accept                             |
| [Design system](design-system.md)                              | Tokens, type, spacing, depth, motion, states, numbers, keyboard, tables, print, icons                                                                                                                                                          | planned                                                                            |

Frontend work can proceed against these now. The parts R1 and R4 decide take effect when `apps/web` is merged into `4ce-core`.

A polish pass on `wp/WP-F-10-polish` departs from the exact-match finish on purpose: softer, rounder corners through new radius tokens, full-pill buttons and search fields, and a flat finish with no added depth ([log](../log/2026/11/2026-11-11-wp-wp-f-10-polish.md)).

## Where the code goes

The layout is fixed by the [repository rules](repository.md#layout):

```
apps/web/
├── package.json, package-lock.json   npm, versions pinned exactly (ADR-0035 §1)
├── README.md
├── src/
│   ├── routes/                pages only: load data, compose components
│   └── lib/
│       ├── ui/                the design system: tokens and base components
│       ├── components/<area>/ feature components (chat/, signoff/, studio/ …)
│       ├── stores/            client state
│       ├── api/               typed API client, generated at build, never committed
│       └── i18n/              UI strings per locale
├── static/                    self-hosted fonts, icons, images
└── tests/
```

- **Naming:** Svelte components PascalCase (`SignOffPanel.svelte`), TypeScript modules camelCase (`trustView.ts`), folders kebab-case.
- **No industry words.** The [neutrality check](repository.md#checks) covers `apps/` too: labels such as "Asset" or "Application" come from the active pack's vocabulary, never from the code.
- **No upstream code.** Components the team wrote in the earlier fork are rebuilt from their behaviour on the new tokens, not copied (ADR-0035 §14).

## The backend contract

**Status: built (slice 1).** `GET /api/openapi.json` is the source of truth, and the types are generated from it with openapi-typescript at build time.

**One origin.** The UI and the API are served from the same host; every API path starts with `/api`. In development, the Vite dev server proxies `/api` to the backend, so the browser still sees one origin.

**The contract is [api.md](api.md).** In short: sign in with `POST /api/auth/signin`; the browser keeps an HttpOnly `fource_token` cookie; send the `fource_csrf` cookie's value as `X-CSRF-Token` on every POST, PUT, PATCH or DELETE; errors are `{"error": {"code", "message"}}`.

### User roles and agent roles are different lists

- **User roles** (who a person is): Admin, Author, Reviewer, Viewer, Auditor, Pack Author, Pack Approver. They come back in `roles` and decide what a person may do.
- **Agent roles** (who did a step of a run): Planner, Reader, Analyst, Author, Challenger, Sign-off (ADR-0035 §5). They label the stage rail.

## Running the backend locally

Sign-in, the session and sign-out come from the server in a dev build, so `npm run dev` needs it running:

```
just setup                                     # once: Python, packages, git hooks, a .env with fresh secrets
just dev                                       # the server on http://127.0.0.1:8000, SQLite, no Docker needed
just create-user you@example.com --role Admin  # once: asks for a password
just web-dev                                   # the web app on http://localhost:5173, /api sent to the server
```

`npm run dev` sends `/api` to `http://127.0.0.1:8000`; set `API_TARGET` to use another server. `VITE_4CE_DEMO=1 npm run dev` runs the fully fake app with no server. To test against PostgreSQL instead, run `just services` and set `FOURCE_DATABASE_URL` in `.env` as `.env.example` shows.

## What to build, in order

1. **The screen inventory** (ADR-0035's follow-up): every screen the pitch demo and Phase 1 need, which becomes the frontend's work packages.
2. **WP-F-09:** design tokens, base components and the app shell, with the `/ui` route that shows every component in every state (ADR-0035 §13).
3. **Sign-in, session and sign-out** against slice 1: the first screens with a real backend ([WP-UI-06, part 1](#wp-ui-06-part-1-sign-in-session-and-sign-out-against-the-server)).
4. **WP-UI-01:** chat, cases and the run view with the stage rail. Runs, cases and live events come in later backend slices; until then, MSW fixtures. Propose each endpoint's shape in a PR to this page, so the backend builds what the screens need.
5. **WP-UI-02** sign-off panel, **WP-UI-03** receipt and provenance, **WP-UI-04** Sovereignty page.

### WP-UI-06, part 1: sign-in, session and sign-out against the server

**Built** ([log](../log/2026/11/2026-11-17-wp-wp-ui-06-sign-in.md)). The first part of [WP-UI-06](web-screens.md#proposed-work-packages), in the master plan's §12 template. The rest of WP-UI-06 (session expiry with the return path, no-access and error pages) needs WP-ID-02 and WP-UI-05, and is written up when it starts.

**Goal:** a person signs in against a real 4CE server, stays signed in across reloads until the token expires, and signs out. Every other screen stays on its stand-in data.

**Interface:**

- `src/lib/data/server.ts`: `serverSession()`, the `DataSource` calls `currentUser`, `signIn`, `signOut`, `setupStatus`, `signUp` and `createFirstAccount` over `fetch`, and `ServerError` (`code`, `status`, `message`).
- `chooseSource` (`src/lib/data/source.ts`): a demo build (`VITE_4CE_DEMO=1`) stays fake throughout; a dev build takes those calls from the server and everything else from the fake replay; a production build is still refused.
- `npm run dev` proxies `/api` to `API_TARGET`, by default `http://127.0.0.1:8000` (`just dev`).

**Inputs and outputs:**

- `signIn(email, password)` sends `POST /api/auth/signin` and answers the person: `name` is `display_name` (the email when that is empty), and `role` is `admin` for the Admin role, `user` otherwise.
- `currentUser()` sends `GET /api/auth/session`: the person on 200, `undefined` on 401 or when no 4CE answer comes back.
- `signOut()` sends `POST /api/auth/signout` with `X-CSRF-Token` set to the `fource_csrf` cookie's current value. 204 and 401 both mean signed out.
- An error answer, `{"error": {"code", "message"}}`, becomes a `ServerError` that carries the server's message. Anything else (no answer, or a status without that envelope, such as the dev proxy's 500 while the server is down) becomes `unreachable`: "Can't reach the 4CE server. Check that it's running, then try again."
- `setupStatus()` answers `{ firstAccount: false }`; `signUp` and `createFirstAccount` refuse, because accounts are made with `fource-server create-user`.
- When sign-out fails, the shell shows the message as an error toast and stays where it is.

**Acceptance tests:**

- Vitest, with `fetch` stubbed (`server.test.ts`, `source.test.ts`):
  1. sign-in posts the email and password as JSON and maps the answer; the password is in no answer, storage or URL;
  2. for `invalid_credentials` (401), `account_locked` (423), `rate_limited` (429) and `rate_limit_unavailable` (503) the error is the server's message, with its code and status;
  3. a rejected `fetch` and a 500 without the envelope are `unreachable`;
  4. the session is the person on 200, and `undefined` on 401 or `unreachable`; it asks with a load function's own `fetch` when given one;
  5. sign-out sends the CSRF cookie's value; 204 and 401 resolve; `csrf_failed` and `unreachable` reject;
  6. `chooseSource`: demo is fake throughout, dev signs in through the server and keeps the fake rest, production is refused.
- Playwright (`e2e/sign-in.spec.ts`), through the dev server against `fource-server`, started with `uv run fource-server migrate` and `serve` on a throwaway SQLite database:
  7. a wrong password shows the server's message, keeps the email and clears the password;
  8. the right password opens the app, a reload stays signed in, and signing out returns to sign-in, where a reload stays;
  9. five wrong passwords lock the account, and the sixth attempt says when to try again.

**Ledger:** nothing new; the server already records every sign-in, failure, lockout and sign-out.

**Files:** `src/lib/data/` (`server.ts`, `source.ts` and their tests), `src/lib/ui/components/AppShell.svelte`, `vite.config.ts`, `playwright.config.ts`, `e2e/` and the README, all under `apps/web/`.

**Docs:** this page, the [web data contract](web-data-contract.md), an ADR for connecting screens one at a time, `state.md` and a work-log entry.

**Neutrality:** no sector terms.

**Out of scope:** the generated client (WP-UI-05); the rest of WP-UI-06; roles other than Admin (WP-ID-02); sign-up and the first account, which the server doesn't offer; the server serving the built UI.

**Depends on:** WP-ID-01 and the sign-in rate limit (WP-F-07), both built. No new dependency.

**Reviewer:** R3.

**Size:** one pull request.

## When `apps/web` lands on `4ce-core`

The first PR that adds `apps/web` also wires it into the repository's checks. In the same PR:

- [ ] **Node 24 LTS** (ADR-0035 §1) in the README's setup and in CI. The README is done (2026-11-04). CI is not: `ci.yml` must add a Node 24 step and a Playwright browser install before `just check` passes there, and that change is for a human.
- [x] **just recipes** for installing (`npm ci`), format, lint and types (prettier, eslint, svelte-check), unit tests (vitest) and browser tests (Playwright), all inside `just check`: `web-install`, `web-format`, `web-lint` (which also runs the design lint), `web-test` (which also runs the icon-generator and design-lint tests), `web-e2e` and `web-dev`. `just setup` runs `npm ci` (2026-11-04).
- [x] **The repo check learns the frontend's naming:** PascalCase components and their `.test.ts` files, SvelteKit's route files, the web app's formatter config and message project, and colocated or `e2e/` tests are accepted by `tools/repo_check.py`, with tests (2026-11-04). Modules stay kebab-case, so there is no camelCase rule.
- [ ] **The licence gate reads the npm SBOM:** generate it with `@cyclonedx/cyclonedx-npm` into `build/sbom/` and pass it to `tools/licence_gate.py`, which already checks any CycloneDX SBOM. ADR-0036 must be decided first.
- [ ] **Dependabot** gains the npm ecosystem, targeting `4ce-core`.
- [ ] **`.gitignore`** gains `apps/web/src/lib/api/` (generated).
- [ ] **The server serves the built UI** (ADR-0035 §2: every path that isn't `/api` returns the fallback page). This is a backend change in `apps/server`; ask the backend stream.
- [ ] **This page** moves from `planned` to `active`, and describes what was built.

## How to work alongside the backend stream

- **Start each session with `just sync`.** Work on a branch named `wp/<WP-id>-<short-title>` off `4ce-core`, never on `4ce-core` itself.
- **Small Conventional Commits** (`feat(web): add the sign-in screen`), `just check` green, then a pull request into `4ce-core` with one work-log entry (`just new-doc log <branch-name>`).
- **Contract changes go through this page.** If a screen needs an endpoint or a field, propose it here first; the backend stream builds to it.
- **Everything else** about working in the repository is in [CONTRIBUTING](../../CONTRIBUTING.md) and the [repository rules](repository.md).
