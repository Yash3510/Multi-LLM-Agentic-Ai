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
- **Diff highlights in dark:** the try-2 diff in "What changed" uses the status tokens (`--color-stop-soft`, `--color-ok-soft`), so it no longer shows light fills in dark.
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

## 2026-11-12: motion on the chat page

**What changed:** hovers read on both grounds (`--color-tint` and `--color-row-hover` are now 6.5 % ink in light and 9 % in dark) and arrive in `instant`, leave in `base` on sidebar rows, message actions and the receipt's two buttons. The details tabs use the sliding highlight (`glide.ts`) for the open tab and the pointer, and a tab's content rises 4 px as it fades in. A message asked or answered in the visit rises 8 px into place; its receipt labels follow 40 ms apart, then the checks and the details panel. Saved threads stay at rest.

**Why:** the frontend owner found the rebuilt chat page still: hovers too faint to see (the dark row hover was black on black), tabs that jump, and nothing arriving.

**Files:** `tokens/theme.css`, `tokens/dark.css`, `Sidebar.svelte`, `message.css`, `ReceiptStrip.svelte`, `DetailsPanel.svelte`, `UserMessage.svelte`, `ResponseMessage.svelte`, `routes/c/[id]/+page.svelte`.

**How it was verified:** in `apps/web`: `npx vitest run` (89 files, 540 tests passed), `npm run lint:design` (clean), `npx svelte-check --threshold error` (0 errors), `npx eslint src/lib/ui src/routes/c` (no findings), `npx prettier --check src/lib/ui src/routes/c` (formatted), `npx playwright test` (8 passed). On `/c/c-demo` in light: the tab marker moved from 0 px to 214 px on a click; a sent message and its reply ran `message-in`; after release the labels ran `label-in` at 0, 40, 80 and 120 ms and the panel `details-in` at 240 ms.

**Decisions:** no new ADR; all of it follows [ADR-0042](../../../adr/0042-motion-language.md) (CSS only, the one spring for the marker's position, reduced motion handled by the existing rule in `app.css`). The two hover tokens move off the measured values of ADR-0041 because those could not be seen.

**Known limits:** unverified: dark theme and reduced motion for this pass, and a hover-by-hover comparison with the old app.

