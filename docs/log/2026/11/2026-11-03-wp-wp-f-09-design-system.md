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
- **[ADR-0037](../../../adr/0037-exact-match-look.md), proposed:** the new app matches the running 4CE app, so its look is measured, not designed.
- **Tokens rewritten to the measured theme:**
  - the measured grey ramp (`gray-50` to `gray-950`) and Tailwind 4's default scales, with the semantic roles as aliases onto the ramp
  - a `dark:` variant keyed on `data-theme`
  - code-block colours measured from the running app on 2026-11-03 (`tokens/code.css`)
- **Premium pass on the base components** (the ADR-0037 amendment), after the owner reviewed a side-by-side and then approved a preview:
  - Lucide icons from `lucide-static` 0.460.0 (ISC). They replace Phosphor and the owned hexagon signature set.
  - 10 px buttons, 12 px fields and menus, 20 px cards.
  - Hairline depth instead of borders, and a soft blue focus glow instead of a ring.
  - A segmented control with a sliding thumb, and 16 px check boxes.
- **design-lint retuned to the look:** blur, translucency, `dark:`, palette classes and scales up to 1.25 are now allowed. Hex colours outside the token files, arbitrary values and drop-shadows are still banned.
- **The contrast test pins every token to its measured value** and keeps three floors: body and verdict text at 4.5:1, and the focus ring at 3:1.

## Why

The owner compared mocks of ADR-0035's new language with the current app, and chose the current app's look. After reviewing the first restyle, the owner asked for more premium icons, outlines and curves. That deviation is recorded in the amendment.

## Files

| Path | Change |
| --- | --- |
| `apps/web/` | New: the app, tokens, components, `/ui` route and tests |
| `tools/design-lint/` | New: the lint, retuned to ADR-0037, with fixtures |
| `tools/icons/` | New: the Lucide icon generator and its tests |
| `docs/adr/0037-exact-match-look.md` | New ADR and amendment |
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
- **Visual:** `/ui` was compared side by side with the running app at :5173 (Settings › Account). The owner reviewed a preview of the premium pass and approved it.

## Decisions

- [ADR-0037](../../../adr/0037-exact-match-look.md) and its amendment, proposed; R1's acceptance is pending.
- The owner approved retuning design-lint and the contrast test, and adding `lucide-static` (ISC).

## Docs updated

- ADR-0037 is new.
- `web-screens.md` is new.

## Known limits and follow-ups

No issue numbers yet; each item needs one opened before the PR.

- `design-system.md` still describes ADR-0035's language and needs rewriting to point at ADR-0037.
- The OLED dark theme is planned, not built.
- The on/off setting is still a segmented control; the measured app uses a switch.
- Surfaces (menu panels, cards, dialogs) have not had the premium pass.
- The `/ui` explanation text still describes the old rules.
- The pixel check against the running app is not automated yet.
