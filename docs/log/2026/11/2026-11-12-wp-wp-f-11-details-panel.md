---
title: "apps/web: one details panel and soft glass surfaces"
type: log
status: implemented
owner: R3
updated: 2026-11-12
date: 2026-11-12
branch: wp/WP-F-11-details-panel
pr: null
work_package: WP-F-11
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: one details panel and soft glass surfaces

## What changed

- **One details panel:** the rows under a released answer (Full provenance, each agent's output, Execution timeline, Sources) are one panel with four tabs: Provenance, Reasoning, Timeline, Sources. Each tab shows its count and is hidden when empty. The timeline draws each step as nodes on a wire, in ink.
- **Soft glass for floating surfaces:** menus, popovers, the select list, dialogs, sheets, the side panel, the composer and the top bar take the glass tokens (`tokens/glass.css`). Surfaces in the flow take a soft fill and a top highlight. No accent colour and no glow.
- **Rounder shapes:** `--radius-panel` 20 to 24 px and `--radius-inset` 12 to 14 px.
- **Plain message type:** a sent message uses the body size (15 px, was 16 px) and emphasis in a reply is medium weight (was semibold).
- **Demo chat:** the fake source has a chat, "Details demo", whose run fills every tab: a second try, six agent outputs and a source the answer does not cite.

## Why

The owner found the provenance table and the rows under it hard to read, approved a mock of one tabbed panel, and asked for a softer, rounder, glass finish across the app without violet and without a background glow. The owner also found a sent message and bold text in replies too heavy.

## Files

- `apps/web/src/lib/ui/details.ts`, `details.test.ts`
- `apps/web/src/lib/ui/components/DetailsPanel.svelte`, `ResponseMessage.svelte`, `ReceiptStrip.svelte`, `signoff.test.ts`
- `apps/web/src/lib/ui/components/UserMessage.svelte`, `Composer.svelte`, `TopBar.svelte`, `ListboxPopup.svelte`, `surfaces.css`
- `apps/web/src/lib/ui/tokens/glass.css`, `theme.css`, `index.css`
- `apps/web/src/lib/data/fake.ts`

## How it was verified

Run in `apps/web` on 2026-11-12:

- `npx vitest run`: 89 files, 540 tests passed.
- `npm run lint:design`: clean.
- `npx svelte-check --threshold error`: 0 errors.
- `npx eslint src/lib/ui`: no findings.
- `npx prettier --check src/lib/ui`: all formatted.
- `npx playwright test`: 8 passed.
- Screenshots of `/c/c-demo` in light and dark with the user menu open, and of a newly sent message.

## Decisions

- [ADR-0043](../../../adr/0043-soft-glass-surfaces.md), proposed: glass only where a surface floats over content, through tokens.
- The test of the folded provenance rows in `signoff.test.ts` was replaced by a test of the same content in the new panel, because the rows moved there.
- Where blur is missing or the person asks for less transparency, the glass tokens fall back to the opaque fills.

## Docs updated

- `docs/adr/0043-soft-glass-surfaces.md`, `docs/architecture/design-system.md`, `docs/state.md`.

## Known limits

- Unverified: the settings dialog, sheets and the side panel in dark with the glass fill; only the chat page was checked in both themes.
- The try-2 diff in "What changed" keeps light highlight fills in dark. It predates this change and is not fixed here. No issue is filed yet.
