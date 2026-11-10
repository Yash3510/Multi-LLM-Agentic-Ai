---
title: "apps/web user settings and admin areas"
type: log
status: implemented
owner: R3
updated: 2026-11-10
date: 2026-11-10
branch: wp/WP-F-09-design-system
pr: null
work_package: WP-F-09
author: Pranay Munj
areas: [apps/web, docs/architecture]
tags: [4ce, log, frontend]
---

# apps/web user settings and admin areas

## What changed

- **User settings:** Personalization (memories), Audio, Data Controls, Usage, Archived Chats and Account, each matched to the running app.
- **Admin area:** the admin frame and People list, the add, edit and access-preview dialogs, Groups with the group editor and default permissions, Evaluations (leaderboard and feedback), Functions (read only), and the admin settings tabs in the settings dialog (General, Authentication, Connections, Models, Sub-agents, Interface, Audio, Images, Evaluations, Analytics, Documents, Code Execution, Pipelines, Database).
- **Data contract:** the fake data source and [web-data-contract.md](../../../architecture/web-data-contract.md) gained the calls these screens use, including an admin ledger that every admin change writes.

## Why

The new app has to match the running 4CE app area by area (ADR-0041), and the owner's rules for the admin area keep it safe until the API exists: fake data only, local or self-hosted options only, typed confirmations for destructive actions, and Functions shown read only.

## Files

`apps/web/src/lib/data/{types,fake,fake.test}.ts`, `apps/web/src/lib/ui/*.ts` (rules and their tests), `apps/web/src/lib/ui/components/*` (pages, dialogs, admin panels and their tests), `apps/web/src/routes/admin/**`, `apps/web/src/lib/ui/tokens/*` (role and chart colours), `apps/web/src/lib/ui/icons/registry.json`, `docs/architecture/web-data-contract.md`.

## How it was verified

- `vitest run` in `apps/web`: 486 tests passed. `lint:design`, `svelte-check --threshold error`, `eslint .`, `prettier --check .`, `VITE_4CE_DEMO=1 npm run build`, the tools tests (16 passed), `repo_check`, `neutrality_check` and `docs_check` all passed.
- Each screen was captured beside the running app at 1280 by 800 and scored per pixel (tolerance 24). Most screens score 98 to 99.9 %; lower scores come from parts left out by owner decision (listed below).

## Decisions

- Owner rules for admin (2026-11-10): fake source only; auth items with fake checks, LDAP and OAuth shown as configured by the server; only local or self-hosted options; typed confirmation, undo where possible and a ledger entry for destructive actions; Functions UI only.
- Left out because they reach outside or are upstream-only: Web Search, cloud speech, image and document providers, Direct Connections, Import From Link, function sharing and support links, the licence upsell and community sharing. Connections accept only local or private addresses.
- Charts are drawn as plain SVG; no chart package was added.

## Docs updated

`docs/architecture/web-data-contract.md`, `docs/state.md`.

## Known limits

- Calls are fake: saving functions, pulling models, maintenance and exports run against the fake source only.
- Not built yet: the people pager, per-person chats, avatar editing in the admin editor, group member CSV import, ComfyUI workflows, banners and default interface settings in admin General.
