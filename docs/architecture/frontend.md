---
title: Frontend
type: architecture
status: planned
owner: R3
updated: 2026-10-24
covers:
  - apps/web/
tags: [4ce, architecture, frontend]
---

# Frontend

Everything needed to build `apps/web`, the 4CE web UI and Pack Studio, independently of the backend work. **Pranay, the frontend owner, develops it.** The backend stream builds the server and the database on `4ce-core` at the same time. The two meet at one contract: the server's OpenAPI document.

The web UI is not built yet; the backend contract below is. This page is the starting point and the working agreement.

## What is already decided

| Record | Decides | Status |
| --- | --- | --- |
| [ADR-0035](../adr/0035-frontend-foundations.md) | Stack and exact versions, static serving from the server, live updates, the fake API until the backend lands, roles and labels, devices, languages, theme, accessibility, no glass, icons, quality gates, clean room | proposed; accepted by the frontend owner; R1 to accept §2 (serving) and §5 (roles) |
| [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) | How the licence gate treats MPL-2.0 build and test tools (lightningcss, axe-core) and permissive licences Appendix A doesn't name | proposed; R4 to accept before `apps/web` lands on `4ce-core` |
| [Design system](design-system.md) | Tokens, type, spacing, depth, motion, states, numbers, keyboard, tables, print, icons | planned |

Frontend work can proceed against these now. The parts R1 and R4 decide take effect when `apps/web` is merged into `4ce-core`.

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

Once slice 1 has landed:

```
just setup                                     # once: Python, packages, git hooks, a .env with fresh secrets
just dev                                       # the server on http://127.0.0.1:8000, SQLite, no Docker needed
just create-user you@example.com --role Admin  # once: asks for a password
```

Point the Vite proxy at `http://127.0.0.1:8000`. To test against PostgreSQL instead, run `just services` and set `FOURCE_DATABASE_URL` in `.env` as `.env.example` shows.

## What to build, in order

1. **The screen inventory** (ADR-0035's follow-up): every screen the pitch demo and Phase 1 need, which becomes the frontend's work packages.
2. **WP-F-09:** design tokens, base components and the app shell, with the `/ui` route that shows every component in every state (ADR-0035 §13).
3. **Sign-in, session and sign-out** against slice 1: the first screens with a real backend.
4. **WP-UI-01:** chat, cases and the run view with the stage rail. Runs, cases and live events come in later backend slices; until then, MSW fixtures. Propose each endpoint's shape in a PR to this page, so the backend builds what the screens need.
5. **WP-UI-02** sign-off panel, **WP-UI-03** receipt and provenance, **WP-UI-04** Sovereignty page.

## When `apps/web` lands on `4ce-core`

The first PR that adds `apps/web` also wires it into the repository's checks. In the same PR:

- [ ] **Node 24 LTS** (ADR-0035 §1) in the README's setup and in CI.
- [ ] **just recipes** for installing (`npm ci`), format, lint and types (prettier, eslint, svelte-check), unit tests (vitest) and browser tests (Playwright), all inside `just check`.
- [ ] **The repo check learns the frontend's naming:** today it rejects upper-case file names, so `SignOffPanel.svelte`, camelCase `.ts` modules and SvelteKit's `+page.svelte` need rules in `tools/repo_check.py`, with tests.
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
