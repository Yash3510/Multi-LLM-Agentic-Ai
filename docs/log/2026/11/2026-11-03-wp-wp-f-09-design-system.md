---
title: "apps/web design system on the measured look"
type: log
status: implemented
owner: R3
updated: 2026-11-03
date: 2026-11-03
branch: wp/WP-F-09-design-system
pr: null
work_package: WP-F-09
author: Pranay Munj
areas: [apps/web, tools/design-lint, tools/icons, docs/adr, docs/architecture]
tags: [4ce, log, frontend]
---

# apps/web design system on the measured look

## What changed

- **apps/web lands on the branch:** the SvelteKit scaffold, tokens, number formats, icons, the `/ui` reference route and the base components (actions, fields, status, surfaces). It was built in earlier sessions and is committed here for the first time.
- **[ADR-0041](../../../adr/0041-exact-match-look.md), proposed:** the new app matches the running 4CE app, so its look is measured, not designed.
- **Tokens rewritten to the measured theme:**
  - the measured grey ramp (`gray-50` to `gray-950`) and Tailwind 4's default scales, with the semantic roles as aliases onto the ramp
  - a `dark:` variant keyed on `data-theme`
  - code-block colours measured from the running app on 2026-11-03 (`tokens/code.css`)
- **Premium pass on the base components** (the ADR-0041 amendment), after the owner reviewed a side-by-side and then approved a preview:
  - Lucide icons from `lucide-static` 0.460.0 (ISC). They replace Phosphor and the owned hexagon signature set.
  - 10 px buttons, 12 px fields and menus, 20 px cards.
  - Hairline depth instead of borders, and a soft blue focus glow instead of a ring.
  - A segmented control with a sliding thumb, and 16 px check boxes.
- **design-lint retuned to the look:** blur, translucency, `dark:`, palette classes and scales up to 1.25 are now allowed. Hex colours outside the token files, arbitrary values and drop-shadows are still banned.
- **Repository wiring, 2026-11-04:**
  - 4ce-core is merged in, and the ADR is renumbered to 0041 (4ce-core uses 0037).
  - `apps/web` is excluded from the uv workspace.
  - The repo check accepts the web app's names (PascalCase components and their tests, SvelteKit route files, its formatter config and message project, colocated and `e2e/` tests).
  - `just` gains `web-install`, `web-format`, `web-lint`, `web-test`, `web-e2e` and `web-dev`. The lint, test and e2e recipes are part of `just check`, and `just setup` runs `npm ci`.
- **Surfaces premium pass, 2026-11-04:**
  - Cards have a hairline edge and a 20 px radius. Hover lifts them to e1, a press scales them to 0.99, and a selected card sits sunken with a line-2 ring.
  - Floats are borderless with a 12 px radius. Tooltips are a near-black chip.
  - Menu rows are 28 px with an 8 px radius. The keyboard highlight is the tint with a thin focus edge.
  - The current tab carries a 2 px ink edge instead of the accent fill.
  - Tab and disclosure hovers use the tint, and focus is the soft glow instead of an outline.
  - Accordion and separator rules are hairlines.
- **List parts, 2026-11-04 (layout look §4.2, §4.4, §9.2):**
  - `timeGroup` and `formatAgo` in `format.ts` give each row its recency band (counted in calendar days) and a short time-ago (`1m` to `Ny`, never under a minute, units localised by Intl).
  - New components: `GroupHeading` (a real heading), `SortHeader` (with `aria-sort`, and a hidden caret on unsorted columns so labels stay aligned, using `sort.ts`), and `ListRow` (side list and list-dialog sizes, tint hover, a current state).
  - A new `/ui` Lists section shows them. Its recency headings only appear while sorted by time.
  - The `ListboxPopup` float is borderless at a 12 px radius. The chosen option is marked by the tick at medium weight, not the accent fill. The keyboard highlight is the tint with a blue inner edge, with a forced-colours outline.
  - The `Pill` copy button's focus is the glow.
- **Icons, menus and the shell, 2026-11-04:**
  - Icons switched to `@phosphor-icons/core` 2.1.1 (MIT); `lucide-static` was removed. Each name maps to the glyph and weight the running app uses in that place. These were found by matching its rendered SVG paths against the package, not by reading its code; the bold places are the row dots, the carets, back, minus and send.
  - Sizes are 16 px in rows and 18 px in the sidebar and top bar. Quiet icon buttons are gray-600 / gray-400 and turn ink on the tint.
  - The generator writes the MIT notice as a legal comment on the path table, and `vite.config.ts` keeps legal comments in the minified build.
  - Menus match common look F12 exactly.
  - New `Sidebar` (open panel and 42 px rail), `TopBar`, `Logomark` and `sidebar-width.ts`, plus a `/ui` Shell section with the chat menu.
  - Logomark files come from the owner's brand kit (`~/Downloads/4CE-brand-kit/`). They are byte-identical copies (SHA-256 checked), with only the file names lower-cased for the repo's naming rule. The repo has no asset register: the licence gate lists only review-required packages, and MIT is on the allow list.
- **The contrast test pins every token to its measured value** and keeps three floors: body and verdict text at 4.5:1, and the focus ring at 3:1.

## Why

The owner compared mocks of ADR-0035's new language with the current app, and chose the current app's look. After reviewing the first restyle, the owner asked for more premium icons, outlines and curves. That deviation is recorded in the amendment.

## Files

| Path | Change |
| --- | --- |
| `apps/web/` | New: the app, tokens, components, `/ui` route and tests |
| `tools/design-lint/` | New: the lint, retuned to ADR-0041, with fixtures |
| `tools/icons/` | New: the Lucide icon generator and its tests |
| `docs/adr/0041-exact-match-look.md` | New ADR and amendment |
| `docs/architecture/web-screens.md` | New: the screen inventory |
| `docs/architecture/design-system.md` | Edited in an earlier session; it still describes ADR-0035's language (see Known limits) |
| `.gitignore` | Ignores the web build, test output and generated icon and message files |

## How it was verified

All run in `apps/web` on 2026-11-03:

- `npx vitest run`: 17 files, 174 tests passed. Before the premium pass, 209 passed; the 35 tests of the dropped signature set were removed with it.
- `npx vitest run ../../tools --root ../..`: 10 tests passed (icon generator 5, design lint 5).
- `npm run lint:design`: clean.
- `npm run check`: 1040 files, 0 errors, 0 warnings.
- `npm run lint`: eslint clean, and prettier reports every file formatted.
- `npm run build`: the static site was written.
- 2026-11-04, after the surfaces pass: `npx vitest run` (174 passed), `lint:design` clean, `svelte-check` 0 errors, eslint and prettier clean, and `npm run build` succeeded. From the repo root, `repo_check.py`, `neutrality_check.py` and `docs_check.py --base origin/4ce-core` all exited 0.
- 2026-11-04, after the list parts: `npx vitest run` (19 files, 192 tests), the tools tests (10), `lint:design`, `svelte-check`, `npm run lint` and `npm run build` all passed. From the repo root, `repo_check.py`, `neutrality_check.py` and `docs_check.py --base origin/4ce-core` exited 0.
- 2026-11-04, after icons, menus and shell: `npx vitest run` (20 files, 200 tests), the tools tests (12), `lint:design`, `svelte-check`, eslint, prettier and `npm run build` all passed. The build chunk under `build/_app/immutable/chunks/` carries the full Phosphor MIT notice (checked with `grep -rl 'Copyright (c) 2023 Phosphor Icons' build`). `repo_check.py`, `neutrality_check.py` and `docs_check.py --base origin/4ce-core` exited 0.
- **Visual:** `/ui` was compared side by side with the running app at :5173 (Settings › Account). The owner reviewed a preview of the premium pass and approved it.

## Decisions

- [ADR-0041](../../../adr/0041-exact-match-look.md) and its amendment, proposed; R1's acceptance is pending.
- The owner approved retuning design-lint and the contrast test, and adding `lucide-static` (ISC).

## Docs updated

- ADR-0041 is new.
- `web-screens.md` is new.

Also run on 2026-11-04, after the merge:

- `uv run pytest tools`: 116 passed.
- `tools/repo_check.py`, `tools/neutrality_check.py` and `tools/docs_check.py --base origin/4ce-core`: clean.
- **The new recipes' commands, run from the repository root** (`just` is not installed locally):
  - `npm --prefix apps/web run lint`, `lint:design` and `check`: clean.
  - `npm --prefix apps/web test`: 174 passed.
  - `npm --prefix apps/web exec -- vitest run --root . --dir tools`: 10 passed.
  - `npm --prefix apps/web run e2e`: 4 passed in 14.9 s.

## Known limits and follow-ups

No issue numbers yet; each item needs one opened before the PR.

- `design-system.md` still describes ADR-0035's language and needs rewriting to point at ADR-0041.
- The OLED dark theme is planned, not built.
- The on/off setting is still a segmented control; the measured app uses a switch.
- The recency bands match the measured app. The `avoid.md` lists flag them, but HANDOFF records that those lists no longer steer the look.
- The pointer highlight in menus and the select list (gray-50 at 60 %) is barely visible on white. It is the measured value, kept for now.
- Sidebar resizing (220 to 480 px) and the phone drawer are planned; `sidebarWidth` already clamps a stored width.
- The `/ui` explanation text still describes the old rules.
- The pixel check against the running app is not automated yet.
- CI (`ci.yml`) has no Node 24 or Playwright browser step, so `just check` will fail there until a human adds them.
- The npm SBOM is not in the licence gate yet; that waits on ADR-0036.
- Dependabot has no npm entry.
- The server does not serve the built UI yet.
