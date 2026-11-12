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

Checked afterwards on `/c/c-demo`: in dark the row hover and tint resolve to 9 % white on the `#0d0d0d` sidebar and the tab marker shows on the panel; with `data-motion="reduce"` the marker and tab content change place without a transition, a sent message and its reply run no animation, and hovers fade in 120 ms.

**Known limits:** unverified: a hover-by-hover comparison with the old app.


## 2026-11-12: hover and press timing against the running app

**What changed:** hover, press and focus now change in `interact`, 150 ms, on `--ease-standard`, the same in and out; a component sets `--interact-duration` for the running app's other timings (100 ms on the sidebar's section buttons, 200 ms on the voice button and cards). The logo mark turns 120° when its link or the welcome hero is hovered. Every chat row shows its menu button on hover in place of the age. The composer's tools, dictation and model ink darken on hover. An interactive card rises 1 px.

**Why:** measured side by side, the running app's hovers take 150 ms (some 100 ms) and ours took 240 ms on a soft ease-out on the way out, so the app felt laggy; several hover states the running app has were missing.

**Files:** `app.css`, `tokens/motion.css`, `motion.svelte.ts`, `motion.test.ts`, `tokens/surfaces.css`, `Sidebar.svelte`, `message.css`, `ReceiptStrip.svelte`, `DetailsPanel.svelte`, `Pill.svelte`, `Logomark.svelte`, `AppShell.svelte`, `Composer.svelte`, `Card.svelte`, `routes/+page.svelte`.

**How it was verified:** the new check in `motion.test.ts` failed before the change and passes after. In `apps/web`: `npx vitest run` (89 files, 541 tests passed), `npm run lint:design` (clean), `npx svelte-check --threshold error` (0 errors), `npx eslint src/lib/ui src/routes/c` (no findings), `npx prettier --check src/lib/ui src/routes/c` (formatted), `npx playwright test` (8 passed). Read from the running page: a sidebar row transitions in 0.15 s on `cubic-bezier(0.4, 0, 0.2, 1)`; the mark's `rotate` is `120deg` under hover; the row menu's opacity goes 0 to 1 and the age to 0; the section button transitions in 0.1 s. Hover-and-click clips of the sidebar, composer, settings and a card were recorded on both apps and joined side by side (local, not committed).

**Decisions:** [ADR-0042](../../../adr/0042-motion-language.md) §3 and §7 amended: 150 ms and 100 ms interactions, lift and shadow where the running app has them, and the one rotation for the logo mark, which is rotated and never redrawn.

**Docs updated:** `docs/adr/0042-motion-language.md`, `docs/architecture/design-system.md`, `docs/state.md`.

**Known limits:** the per-row chat menu buttons have no action yet, like the one before them. No shortcut hints on New Chat and Search, because the shortcuts are not wired. The interactive card is only used on `/ui`, so the lift shows nowhere else yet. The top bar's button hover still differs from the running app's. Unverified: the new hovers in dark, beyond the composer's ink.


## 2026-11-13: toasts and the settings dialog

**What changed:** toasts sit on the soft glass surface and wait while the pointer or focus is on them. The settings dialog is a card of at most 920 by 640 px with a close button, a Personal and Admin switch for admins, one level of headings, a filled icon on the open tab and a fade where the list scrolls. The General page is grouped into Appearance, Language, System prompt and Advanced; Theme is a segmented control with icons, the system prompt a multi-line box, model parameters a disclosure row, and the save bar shows only when something changed and confirms with a toast. The theme picker's emoji are gone. The icon generator accepts the `fill` weight.

**Why:** the frontend owner found the toasts off the current look and the settings dialog poor, and approved six suggestions for it.

**Files:** `tools/icons/generate.mjs`, `tools/icons/generate.test.mjs`, and in `apps/web/src/lib/ui`: `icons/registry.json`, `toast.svelte.ts`, `toast.test.ts`, `settings-nav.ts`, `settings-nav.test.ts`, `settings-draft.ts`, `settings-draft.test.ts`, `components/Toaster.svelte`, `components/SettingsDialog.svelte`, `components/SettingsGeneral.svelte`, `components/SegmentedControl.svelte`, `components/settings-page.css`, `components/settings-view.test.ts`, `components/admin-settings-view.test.ts`.

**How it was verified:** the tests for the two new modules were written first. In `apps/web`: `npx vitest run` (550 tests passed), `npm run lint:design` (clean), `npx svelte-check --threshold error` (0 errors), `npx eslint src/lib/ui` (no findings), `npx prettier --check src/lib/ui` (formatted), `npx playwright test` (8 passed), `npm run build` (built), `npx vitest run --root ../.. tools/icons` (7 passed). Screenshots of the dialog were read in light, dark, with the save bar showing, and at 400 px wide.

**Decisions:** [ADR-0041](../../../adr/0041-exact-match-look.md) amended (2026-11-13): the dialog, the filled icon for a selected state and the grouped General page leave the exact match. No new package.

**Docs updated:** `docs/adr/0041-exact-match-look.md`, `docs/state.md`.

**Known limits:** only the General page has the grouped rows and the on-change save bar; the other settings and admin pages keep their old rows and an always-visible Save. Saving is still local to the page, as before. The content column is about 648 px, not the 600 px suggested. Unverified: the admin side in dark.
