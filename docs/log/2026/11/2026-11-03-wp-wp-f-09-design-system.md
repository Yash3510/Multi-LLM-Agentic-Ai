---
title: "apps/web design system on the measured look"
type: log
status: implemented
owner: R3
updated: 2026-11-10
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

| Path                                 | Change                                                                                  |
| ------------------------------------ | --------------------------------------------------------------------------------------- |
| `apps/web/`                          | New: the app, tokens, components, `/ui` route and tests                                 |
| `tools/design-lint/`                 | New: the lint, retuned to ADR-0041, with fixtures                                       |
| `tools/icons/`                       | New: the Lucide icon generator and its tests                                            |
| `docs/adr/0041-exact-match-look.md`  | New ADR and amendment                                                                   |
| `docs/architecture/web-screens.md`   | New: the screen inventory                                                               |
| `docs/architecture/design-system.md` | Edited in an earlier session; it still describes ADR-0035's language (see Known limits) |
| `.gitignore`                         | Ignores the web build, test output and generated icon and message files                 |

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

## 2026-11-10: user settings and admin areas

### What changed

- **User settings:** Personalization (memories), Audio, Data Controls, Usage, Archived Chats and Account, each matched to the running app.
- **Admin area:** the admin frame and People list, the add, edit and access-preview dialogs, Groups with the group editor and default permissions, Evaluations (leaderboard and feedback), Functions (read only), and the admin settings tabs in the settings dialog (General, Authentication, Connections, Models, Sub-agents, Interface, Audio, Images, Evaluations, Analytics, Documents, Code Execution, Pipelines, Database).
- **Data contract:** the fake data source and [web-data-contract.md](../../../architecture/web-data-contract.md) gained the calls these screens use, including an admin ledger that every admin change writes.

### Why

The new app has to match the running 4CE app area by area (ADR-0041), and the owner's rules for the admin area keep it safe until the API exists: fake data only, local or self-hosted options only, typed confirmations for destructive actions, and Functions shown read only.

### Files

`apps/web/src/lib/data/{types,fake,fake.test}.ts`, `apps/web/src/lib/ui/*.ts` (rules and their tests), `apps/web/src/lib/ui/components/*` (pages, dialogs, admin panels and their tests), `apps/web/src/routes/admin/**`, `apps/web/src/lib/ui/tokens/*` (role and chart colours), `apps/web/src/lib/ui/icons/registry.json`, `docs/architecture/web-data-contract.md`.

### How it was verified

- `vitest run` in `apps/web`: 486 tests passed. `lint:design`, `svelte-check --threshold error`, `eslint .`, `prettier --check .`, `VITE_4CE_DEMO=1 npm run build`, the tools tests (16 passed), `repo_check`, `neutrality_check` and `docs_check` all passed.
- Each screen was captured beside the running app at 1280 by 800 and scored per pixel (tolerance 24). Most screens score 98 to 99.9 %; lower scores come from parts left out by owner decision (listed below).

### Decisions

- Owner rules for admin (2026-11-10): fake source only; auth items with fake checks, LDAP and OAuth shown as configured by the server; only local or self-hosted options; typed confirmation, undo where possible and a ledger entry for destructive actions; Functions UI only.
- Left out because they reach outside or are upstream-only: Web Search, cloud speech, image and document providers, Direct Connections, Import From Link, function sharing and support links, the licence upsell and community sharing. Connections accept only local or private addresses.
- Charts are drawn as plain SVG; no chart package was added.

### Docs updated

`docs/architecture/web-data-contract.md`, `docs/state.md`.

### Known limits

- Calls are fake: saving functions, pulling models, maintenance and exports run against the fake source only.
- Not built yet: the people pager, per-person chats, avatar editing in the admin editor, group member CSV import, ComfyUI workflows, banners and default interface settings in admin General.

## 2026-11-10 (later): notes, channels, calendar, automations and playground

### What changed

- Notes list and editor (autosave, word and character counts, Enhance streamed from the fake source, delete with Undo).
- Channels: list (admins create; delete needs the name typed and is logged) and the channel view with reactions, replies, pins, edits, confirmed deletes and a simulated typing indicator.
- Calendar month view with events, playground (chat, completions, images notice), automations list and editor.
- Sidebar entries for Channels, Calendar and Automations follow the admin General switches; the user menu gains Playground.

### How it was verified

The project check (vitest 504 passed, design-lint, svelte-check, eslint, prettier, build, tools tests, repo, neutrality and docs checks) passed. Scores against :5173: notes list 99.53 %, playground 99.63 %, calendar 98.61 %; channels and automations are off on :5173 and were built from the old code.

### Decisions

Owner rules for this round: fake data only; webhooks, outside share links, outside calendar sync and web search left out; presence and typing simulated; AI features use the fake stream; deletes need a typed confirmation or offer Undo.

### Known limits

Not built yet: channel threads and the emoji picker, calendar week and day views, recurring events, note recording and chat, the playground's parameters panel.

## 2026-11-10 (later): gaps closed and a rich-text note editor

### What changed

- Channel threads and an emoji picker; calendar week and day views with repeating events; note import, playground parameters and a custom automation schedule; the admin leftovers (people pager and chats, avatar choice, group member CSV import, banners, default interface settings, ComfyUI workflow upload, arena models).
- The note editor is now rich text (Tiptap), reading and writing Markdown so stored notes stay plain text.

### Packages added (owner approved)

- `@tiptap/core`, `@tiptap/pm`, `@tiptap/starter-kit`, `@tiptap/extension-placeholder`, `@tiptap/markdown` 3.32.0, all MIT; the 47 packages in their tree are MIT.
- Earlier on this branch: CodeMirror 6 (`codemirror`, `@codemirror/lang-python`, `@codemirror/theme-one-dark`), MIT, for the tool and function editors.

### How it was verified

The project check passed (vitest, design-lint, svelte-check, eslint, prettier, build, tools tests, repo, neutrality and docs checks). The note editor scores 99.57 % (light) and 99.54 % (dark) against :5173, using one empty test note created on the local :5173 and deleted straight after.

## 2026-11-11 Final parity pass

### What changed

- Below 768 px the icon rail gives way to one sidebar button in the corner (above the sticky top bar), the open sidebar lies over the page, and each page's top bar starts after the button, as in the running app.
- In Settings, Back and the tabs share one row on narrow screens, scrolled to the open tab.

### How it was verified

The project check passed (516 unit tests, 16 e2e, design-lint, svelte-check, eslint, prettier, build, repo, neutrality and docs checks). Every screen was captured against :5173 in light, dark and at 390 × 844, and compared at tolerance 24 (`.parity/pixel/compare.py`). The runner scores only captures newer than the run, after a stale image hid a failed capture once.

| Screen             | Light | Dark  | Phone |
| ------------------ | ----- | ----- | ----- |
| home               | 99.02 | 99.07 | 97.12 |
| ws-models          | 99.95 | 99.94 | 99.90 |
| ws-knowledge       | 99.56 | 99.55 | 99.28 |
| ws-prompts         | 99.97 | 99.96 | 99.96 |
| ws-skills          | 99.97 | 99.96 | 99.96 |
| ws-tools           | 99.55 | 99.55 | 99.06 |
| us-general         | 98.87 | 98.81 | 99.23 |
| us-interface       | 98.13 | 98.07 | 96.68 |
| us-notifications   | 98.99 | 98.93 | 99.24 |
| us-keyboard        | 97.83 | 97.70 | 97.70 |
| us-personalization | 98.97 | 98.91 | 99.56 |
| us-audio           | 98.77 | 98.70 | 98.91 |
| us-data            | 98.97 | 98.90 | 99.54 |
| us-usage           | 98.62 | 98.22 | 97.31 |
| us-archived        | 98.97 | 98.89 | 99.19 |
| us-account         | 98.77 | 98.66 | 98.57 |
| ad-users           | 99.41 | 99.34 | 98.60 |
| ad-groups          | 99.95 | 99.92 | 99.90 |
| ad-evals           | 99.63 | 99.60 | 97.77 |
| ad-feedback        | 99.74 | 99.70 | 98.84 |
| ad-functions       | 99.90 | 99.85 | 98.65 |
| ad-fncreate        | 96.30 | 96.19 | 89.66 |
| as-general         | 96.25 | 96.21 | 90.90 |
| as-auth            | 98.56 | 98.52 | 98.31 |
| as-connections     | 98.10 | 98.04 | 96.85 |
| as-models          | 98.27 | 98.19 | 97.07 |
| as-subagents       | 98.98 | 98.92 | 99.25 |
| as-interface       | 97.52 | 97.46 | 95.41 |
| as-audio           | 97.64 | 97.60 | 95.12 |
| as-images          | 97.45 | 97.41 | 95.03 |
| as-evaluations     | 99.12 | 99.06 | 99.58 |
| as-analytics       | 97.21 | 97.04 | 94.63 |
| as-documents       | 99.08 | 99.02 | 99.19 |
| as-code            | 99.14 | 99.08 | 99.52 |
| as-pipelines       | 99.15 | 99.09 | 99.30 |
| as-database        | 99.13 | 99.06 | 99.46 |
| notes              | 99.53 | 99.48 | 98.59 |
| playground         | 99.62 | 99.53 | 97.86 |
| completions        | 99.82 | 99.77 | 99.26 |
| calendar           | 98.60 | 98.37 | 98.00 |

Known gaps: the function editor starts from 4CE's own example; licence, community sharing and Web Search are left out by the owner's rules; :5173 shows a sign-in toast on the calendar.
