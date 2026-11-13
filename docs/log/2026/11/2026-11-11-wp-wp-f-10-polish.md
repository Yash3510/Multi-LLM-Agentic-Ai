---
title: "apps/web polish pass: softer, rounder, flat"
type: log
status: implemented
owner: R3
updated: 2026-11-11
date: 2026-11-11
branch: wp/WP-F-10-polish
pr: 2
work_package: WP-F-10
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web polish pass: softer, rounder, flat

## What changed

- **Rounder surfaces through tokens:** new corner tokens (`--radius-menu` 18, `--radius-row` 12, `--radius-tile` 10, `--radius-composer` 28, `--radius-checks` 18). Buttons, filters and search fields go full pill; menus, menu rows, sidebar rows, icon tiles, the composer and the checks card take the larger corners.
- **Flat finish:** no shadows or gloss are added. Search fields on every list page and in Settings sit in a flat round tint with a hairline ring (`--field-inset-fill`, `--field-inset-edge`). Quiet icon buttons hover on a white tile with a hairline edge.
- **Provenance rows refined in place:** the same folds in the same order, with more contrast, a hairline between rows, the model in Plex Mono and the verdict (PASS/FAIL) in its colour (`fold-title.ts`, tested). The Sources row lines up with them, shows its count in mono and takes the same caret.
- **Tab hint:** the home composer shows the first suggestion as its placeholder with a Tab key cap; Tab fills it in (the existing Accept shortcut). With text in the box, Tab moves focus as usual (tested).
- **Contrast:** the "Checked" pill's text now passes AA in dark.

## Why

The owner approved this finish from before/after images: keep the current design and only refine it, softer and rounder, with no added depth. An earlier gloss finish was built and then removed at the owner's request because it read as depth.

## Files

`apps/web/src/lib/ui/tokens/{theme,dark}.css`; shared `actions.css`, `menu.css`, `surfaces.css`, `settings-page.css`, `admin-table.css`; `ListRow`, `Sidebar`, `SettingsDialog`, `Composer`, `ReceiptStrip`, `SourcesBar`, `CalendarView`, `PlaygroundChat`, `PeopleList`, the list pages' searches; `fold-title.ts` and its test; `composer.test.ts`; `routes/+page.svelte`, `routes/workspace/+layout.svelte`.

## How it was verified

The project check passed before each push: vitest 524 of 524, design-lint clean, svelte-check, eslint, prettier, build, tools tests 16 of 16, repo, neutrality and docs checks. Before/after screenshots of chat, home, sidebar, menu, Settings, admin, workspace, calendar and playground were captured at 2× from the running app, in light, plus the chat in dark.

## Decisions

- The polish deliberately departs from the old app's finish (ADR-0041's exact-match look), so the pixel scores against the old app drop on these surfaces; that is intended.
- Finish values live in tokens; components only reference them.

## Docs updated

`docs/state.md`.

## Known limits

- The "jump to latest" pill and a menu key cap for Open Settings were shown in earlier rounds but are not part of the approved set, so they are not built.
- Dark mode was checked on the chat only; the other areas use the same tokens but were not captured in dark (unverified).
