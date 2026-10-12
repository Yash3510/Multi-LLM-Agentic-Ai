---
title: Design system
type: architecture
status: planned
owner: R3
updated: 2026-10-08
covers:
  - apps/web/src/lib/ui/
tags: [4ce, architecture, frontend]
---

# Design system

The 4CE design system: tokens, type, shape, depth, motion, states, icons and the rules that keep them consistent. It is decided in [ADR-0035](../adr/0035-frontend-foundations.md). Everything here is **planned**: no code exists yet. All values are our own; nothing is taken from the upstream project (master plan §2.4).

The bar is set above today's UI. It keeps the calm, slow, premium feel that was approved, and it makes "a checker finds nothing inconsistent" something CI enforces rather than something remembered.

## Principles

1. **Roles, not colours.** Components use semantic tokens (`ink-2`, `line-1`, `caution`), never palette steps or hex values. A lint rejects anything else.
2. **One meaning per colour.**
   - Violet means an agent is working, or keyboard focus.
   - Ink means a human decision.
   - Green, amber and red mean the Rule Engine's PASS, REVIEW and FAIL.
3. **Opaque and flat.** No glass, blur, sheen or gloss. Depth comes from surface steps, hairlines and soft shadows.
4. **Calm motion.** Named durations, no overshoot, no scale bumps, one moving thing per region. Motion means something changed; it is never decoration.
5. **Every state, every time.** No component ships without all of its states, light and dark, reduced motion, Hindi and print.
6. **Numbers are identical everywhere.** One format module, so a receipt, a ledger row and a printout show the same string.

## Tokens

**Three tiers:**

1. **Primitives** (`--ref-*`, OKLCH): never used by components.
2. **Semantic roles,** exposed through Tailwind's `@theme` with the default palette switched off.
3. **Component aliases,** which only point at semantic roles, e.g. `--rail-wire: var(--color-line-control)`.

**Themes** swap the semantic values under `<html data-theme>` with `color-scheme` set. The options are system, light and dark.

### Neutrals: one graphite family

Hue 280 at chroma 0.012 or less, so violet belongs to the same family. Every value is in the sRGB gamut.

| Role             | Light              | Dark               | Use                                              |
| ---------------- | ------------------ | ------------------ | ------------------------------------------------ |
| `surface-page`   | `#f9f9fb`          | `#111114`          | App background                                   |
| `surface-raised` | `#ffffff`          | `#19191d`          | Cards, panels                                    |
| `surface-sunken` | `#f3f3f6`          | `#0d0d10`          | Wells, table headers, read-only fields           |
| `surface-hover`  | `#ededf0`          | `#232428`          | Row and quiet-button hover                       |
| `line-1`         | `#e2e3e6`          | `#2a2b2f`          | Hairlines, card borders                          |
| `line-2`         | `#d2d2d6`          | `#37373d`          | Hover and emphasis borders                       |
| `line-control`   | `#8b8c92` (3.35:1) | `#707179` (3.61:1) | Inputs, checkboxes, the rail's not-reached rings |

### Text

| Role           | Light     | Dark      | Contrast on raised                      |
| -------------- | --------- | --------- | --------------------------------------- |
| `ink-1`        | `#1c1c23` | `#eff0f3` | 16.9:1 / 15.4:1                         |
| `ink-2`        | `#4e4f56` | `#bcbdc3` | 8.15:1 / 9.35:1                         |
| `ink-3`        | `#676870` | `#9d9ea4` | 5.54:1 / 6.56:1                         |
| `ink-disabled` | `#9d9ea2` | `#626368` | Disabled controls only (exempt in WCAG) |

**`ink-3` is the lightest colour allowed for any text,** placeholders and meta text included. A CI test measures every text token on every surface token and fails anything under 4.5:1. The exception is 3:1 for text of 24 px or more, or bold text of 18.66 px or more.

### Violet: live work and focus

| Role          | Light              | Dark               | Use                                                |
| ------------- | ------------------ | ------------------ | -------------------------------------------------- |
| `accent`      | `#7644d9` (5.83:1) | `#af99fb` (7.32:1) | Working state, focus ring, current selection edge  |
| `accent-head` | `#7644d9`          | `#d8d1fc`          | The moving light's head on the stage rail          |
| `accent-tail` | `#a38af2`          | `#8862e5`          | The trailing streak only                           |
| `accent-soft` | `#f0eefe`          | `#282041`          | Selected rows (accent text on it: 5.10:1 / 6.39:1) |

**One glow, and only on the moving light's head:** `0 0 3px` of accent, at 22% in light and 30% in dark. Nothing else glows.

**No violet gradients, washes or backgrounds.** Text selection is accent at 14%. The human gate is always ink, never violet.

### Verdicts and status

These follow the Rule Engine (master plan §7.9).

| Role      | Meaning                                        | Light text / mark / soft          | Dark text / mark      |
| --------- | ---------------------------------------------- | --------------------------------- | --------------------- |
| `ok`      | PASS, released, canary blocked                 | `#1f744f` / `#06915f` / `#e3faed` | `#61d19a`             |
| `caution` | REVIEW, reservation, sent back, needs a person | `#995515` / `#c77618` / `#fef4e0` | `#f5b75b` / `#ed9e2f` |
| `stop`    | FAIL, error, invalid input, chain broken       | `#ba1e20` / — / `#feefef`         | `#f68482`             |

- **Every status is a glyph plus a word, never colour alone.** NO DATA uses its own dashed glyph and the word, in ink.
- **Diffs:** additions use `ok-soft` with `ok` text; deletions use `stop-soft` with `stop` text and a strike-through.
- **File types are neutral tags** with a Phosphor file icon. They never borrow verdict colours.

## Type

**Self-hosted fonts, the same on every host,** with nothing system-first:

- **Inter** variable (weights 400, 500 and 600 only) for UI and prose.
- **IBM Plex Mono** for hashes, ids, commands and code.
- **Noto Sans** per Indian script, as woff2 subsets with `unicode-range`, so only the scripts in use download. Their metrics are overridden to line up with Inter.

| Step      | Size / line height | Weight    | Use                                                                      |
| --------- | ------------------ | --------- | ------------------------------------------------------------------------ |
| `micro`   | 11 / 16            | 500       | Eyebrows, rail labels, tags (uppercase with 0.06em tracking, Latin only) |
| `caption` | 12 / 16            | 400       | Meta text, receipt pills, secondary table text                           |
| `small`   | 13 / 20            | 400       | Dense tables, side columns, secondary buttons                            |
| `ui`      | 14 / 20            | 400 / 500 | Controls, inputs, menus                                                  |
| `body`    | 15 / 24            | 400       | Chat prose                                                               |
| `title`   | 17 / 24            | 600       | Panel titles                                                             |
| `heading` | 20 / 28            | 600       | Page titles                                                              |
| `figure`  | 28 / 32            | 600       | KPI numbers (tabular)                                                    |

**Nothing below 11 px or above 28 px inside the app.**

**Indian scripts:** no uppercase and no letter-spacing (both break conjuncts), and 0.15 more line height. Text is truncated by grapheme cluster, never in the middle of one.

## Numbers, units, times and hashes

**One format module (`lib/ui/format`), used everywhere.**

- **Figures:** tabular and lining figures in the UI; prose keeps proportional figures.
- **Units:**
  - A narrow no-break space separates number and unit: `3.7 s`, `4.5 mm/s`, `20 drop/min`.
  - Units are shown exactly as the pack gives them, never re-derived in the browser.
  - A true minus sign; `±` for tolerances; `≤` and `≥` for limits.
- **Durations:** one decimal under 10 s, whole seconds under 60 s, then `1 min 05 s` and `1 h 05 min`.
- **Numbers:** `Intl.NumberFormat` in the user's locale, en-IN by default (`1,23,456`). `₹` for money, with no implicit exchange rate.
- **Hashes:** 8 hex characters plus `…` wherever space is tight. The full 64 in detail views and print, in groups of four, always copyable.
- **Times:** the viewer's time zone, named on records (`14:05 IST`). ISO 8601 in exports.
- **Tables:** numeric columns are right-aligned, with fixed decimals per column and the unit in the header.

## Space, density and radii

**Spacing:** 2, 4, 6, 8, 12, 16, 20, 24, 32, 40 and 48 px, and nothing else.

**Insets are tokens,** so alignment is structural: `inset-card` 16, `inset-panel` 24, `inset-row` 12.

**Densities,** set with `data-density` on any region:

| Density     | Row height          | Used for                              |
| ----------- | ------------------- | ------------------------------------- |
| comfortable | 40 px               | Chat and approval                     |
| default     | 32 px               | Lists                                 |
| compact     | 28 px, `small` type | Rules, observations and ledger tables |

Hit targets stay at least 24 × 24 px in every density.

| Radius    | Value | Used for                                                |
| --------- | ----- | ------------------------------------------------------- |
| `panel`   | 20    | Docked panels, dialogs, sheets                          |
| `card`    | 16    | Cards in the flow, popovers, menus                      |
| `inset`   | 12    | Wells inside cards, text inputs, KPI tiles, code blocks |
| `control` | 8     | Icon buttons, row hover shapes, thumbnails              |
| `tight`   | 6     | Tags, inline code, diff marks, checkboxes               |
| `pill`    | full  | Buttons, chips, badges                                  |

**When one rounded shape sits inside another,** the inner radius is the outer radius minus the padding between them. No other values are allowed.

## Depth: opaque only

| Level | Use                  | Light                                                              |
| ----- | -------------------- | ------------------------------------------------------------------ |
| `e0`  | Cards in the flow    | `line-1` border, no shadow                                         |
| `e1`  | Hover, raised        | `line-2` border + `0 1px 2px` ink/4% + `0 4px 12px -6px` ink/10%   |
| `e2`  | Popover, menu, peek  | `line-1` border + `0 2px 4px` ink/4% + `0 16px 32px -12px` ink/18% |
| `e3`  | Docked panel, dialog | `0 1px 3px` ink/6% + `0 24px 56px -20px` ink/26%                   |

- **Dark mode** carries depth mainly through lighter surface steps, plus a one-pixel top hairline at white/4%, with shadows at twice the alpha.
- **The scrim is a flat colour.** It takes the page's dark tone (graphite at lightness 0.18) at 45% opacity in light and 65% in dark.
- **Banned by lint:** `backdrop-filter`, `filter: blur`, translucent white panels, sheen gradients and glossy inner highlights.

## Motion

| Token        | Duration | Used for                                                      |
| ------------ | -------- | ------------------------------------------------------------- |
| `instant`    | 100 ms   | Press and colour feedback                                     |
| `quick`      | 160 ms   | Hover, icon swaps                                             |
| `base`       | 240 ms   | Tooltips, chips, focus                                        |
| `calm`       | 360 ms   | Cards entering, popovers, expand and collapse                 |
| `slow`       | 560 ms   | Docking panels, dialogs, page crossfades                      |
| `deliberate` | 900 ms   | Rail state changes: ring closing, mark drawing                |
| `handover`   | 1900 ms  | The rail light's travel (unchanged)                           |
| `ambient`    | 3800 ms  | The violet light pass and the status line's dwell (unchanged) |

**Easings:**

| Easing        | Curve                            | Used for                                                  |
| ------------- | -------------------------------- | --------------------------------------------------------- |
| `ease-out`    | `cubic-bezier(0.22, 1, 0.36, 1)` | Anything arriving                                         |
| `ease-in-out` | `cubic-bezier(0.45, 0, 0.25, 1)` | Moving between two resting states (also the logo's curve) |
| `ease-exit`   | `cubic-bezier(0.4, 0, 1, 1)`     | Anything leaving                                          |
| linear        | —                                | Continuous loops only                                     |

**Exits take about two thirds of the entrance's time.** Staggers are 40 ms, for at most 8 items. Copy feedback holds for 1600 ms.

**Rules:**

- **Shape of motion:**
  - No overshoot and no springs.
  - No element scales above 1 or below 0.96. Entrances are opacity plus at most 8 px of movement.
  - No blur and no rotation in transitions.
- **One moving thing per region at a time.**
- **Expand and collapse** always animate `grid-template-rows` from `0fr` to `1fr` at `calm`. Nothing jumps in height.
- **The signature motions are the only expressive ones,** and they live in one module: the rail handover, the working dots, the ring closing, the mark drawing, the violet light pass and the logo.
- **Every new motion is previewed in the real app,** on a route with a scrubber, before it is built.

**Reduced motion:** one switch, fed by the system setting or a per-user setting, drives both the CSS variables and every Svelte transition.

- Nothing moves or scales.
- Crossfades are 120 ms or less.
- Loops stop on a meaningful still frame. For example, a working stage shows six still violet dots.

## States

**Every component handles all of these,** and the `/ui` route shows each of them:

| State              | Treatment                                                                                                                   |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| default            | —                                                                                                                           |
| hover              | Hover surface, `line-2` border, no movement                                                                                 |
| focus-visible      | 2 px `accent` outline, offset 2 px; inset inside scroll areas and table rows                                                |
| active             | One surface step darker for 100 ms; no scale                                                                                |
| selected / current | `accent-soft` fill, a 2 px accent edge, `ink-1` text                                                                        |
| disabled           | `ink-disabled` text and `line-1` border. Still focusable when a tooltip explains why. Never whole-component opacity.        |
| loading            | The label stays and a six-dot ring leads it; the width is locked. Appears only after 300 ms; shows elapsed time after 10 s. |
| empty              | A static signature icon, a one-line title and one line saying what was checked. At most one action.                         |
| error / invalid    | `stop` border plus a message with an icon below it, wired up for assistive technology                                       |
| read-only          | Sunken fill, a copy affordance, and a "sealed" icon on ledger, audit and released items                                     |

**4CE's own states:**

- **Working:** violet dots and the light pass.
- **Decided:** an ink ring with a tick for released, or a dash for withheld.

**Skeletons:**

- **Shape:** blocks use real line heights and radii, so content replaces them without moving anything.
- **Timing:** they stay still for 300 ms, then show one slow grey sheen at `ambient` speed.
- **Where:** only where the layout is known, never as fake agent output.
- **Spinners:** the six-dot ring replaces every spinner.

## Keyboard

- **A command palette:** Ctrl+K, or ⌘K on Mac.
  - **Sections:** Go to, Actions and Recent.
  - **Search:** it matches titles, case ids, rule ids, clause references and hash prefixes.
  - **Permissions:** results are filtered by role. Approving is never a palette action; it keeps the typed word.
- **Global keys:**
  - `/` searches; `?` opens the shortcut sheet.
  - `g` followed by a letter jumps to a page.
  - `j`/`k` and Enter move through tables; ←/→ move across rail stages.
  - Esc closes the top layer.
- **Dialogs** keep focus inside and return it when they close.
- **Every shortcut ignores keys pressed while an input method is composing.**

## Data tables

**An owned `DataTable` for rules, observations and the ledger.**

**Shared behaviour:**

- **Layout:** compact rows, a sticky sunken header, hairline rules and no zebra stripes.
- **Cells:** right-aligned tabular numbers, with units in the header. Identifiers are in Plex Mono. Status is a glyph plus a word.
- **Interaction:** keyboard row navigation. Rows expand inline instead of hiding details in tooltips.
- **Tools:** sorting, filter chips and saved views. Virtualised beyond about 200 rows.

**Each view's columns:**

| View         | Columns                                                                                                       |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| Rules        | id, parameter, limits with unit and tolerance, clause, pack@version and pack hash, effective date, last fired |
| Observations | subject, parameter, value and unit, rule applied, verdict, link to the evidence page and box                  |
| Ledger       | sequence, time with zone, actor, type, run, input/output hash, previous-hash link, sealed marker              |

**A broken ledger chain** shows as a `stop` row: "entry N was changed after it was written".

## Print

**Receipts, approval records, audit sheets and ledger slices print as records:**

- **Page:** A4 portrait, black on white with 1 px rules. No fills, shadows or animation.
- **The rail** prints as one static line.
- **The full fingerprint** prints in Plex Mono, in groups of four.
- **Header:** the organisation's mark, the classification banner (§7.5) and the document type.
- **Approval block:** who approved, when (with time zone), the fingerprint of what was approved, and the review they were shown (§7.15).
- **Footer:** print time and user, the ledger position, and the QR code (§7.16).

**The layout matches the Word deliverable,** so paper and file agree.

## Icons

**Two sources, one family:**

- **Everyday icons are Phosphor** (MIT, `@phosphor-icons/core` 2.1.1).
  - Regular weight on its 256 grid, stroke 16, which is 1 px at 16 px.
  - Bold at 16 px and below.
- **4CE's own concepts get an owned signature set** on the same grid:
  - stroked centrelines with round caps and joins
  - corner radius 8
  - live area 16–240
  - details under about 48 units drawn solid

**The signature set:**

| Glyph                                 | Concept                           | Drawing (256 grid)                                                                                  |
| ------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------- |
| `verdict-pass`                        | Rule verdict PASS                 | The _cell_ (a true pointy-top hexagon, circumradius 105, centred) with Phosphor's check tick inside |
| `verdict-review`                      | REVIEW                            | The cell with a bar and a dot                                                                       |
| `verdict-fail`                        | FAIL                              | The cell with a cross                                                                               |
| `verdict-no-data`                     | NO DATA                           | The cell dashed (six corner chevrons) with a short bar                                              |
| `rule`                                | A rule with cited limits          | A three-zone band with a pointer above the deciding zone                                            |
| `observation` / `-unsure`             | A reading with its box and number | A box with a numbered tab at its corner; dashed when unsure                                         |
| `pack`                                | A signed pack                     | A line-drawn cube at the logo's true 30°                                                            |
| `skill`                               | A skill (guides, never decides)   | A cube body with its lid lifted                                                                     |
| `ledger`                              | The hash chain                    | Three rings on a spine, entry lines, a solid head dot                                               |
| `evidence-pack`                       | The offline-verifiable bundle     | An archive box with a seal ring instead of a slot                                                   |
| `sign-off` / `-pending` / `-returned` | Approval by a named person        | A ring with a tick over a signature line; dashed while pending, a dash when returned                |
| `challenger`                          | The Challenger role               | A tick followed by a question mark                                                                  |
| `unverified`                          | "Could not check"                 | A dashed ring with a question mark                                                                  |

**Roles use Phosphor glyphs:**

| Role       | Icon                    |
| ---------- | ----------------------- |
| Planner    | `path`                  |
| Reader     | `scan`                  |
| Analyst    | `list-magnifying-glass` |
| Author     | `pen-nib`               |
| Challenger | owned `challenger`      |
| Sign-off   | owned `sign-off`        |

**Phosphor also covers:**

| Concept            | Icon                      |
| ------------------ | ------------------------- |
| Subject            | `cube-focus`              |
| Case history       | `clock-counter-clockwise` |
| Calculation        | `math-operations`         |
| Fingerprint        | `fingerprint-simple`      |
| QR                 | `qr-code`                 |
| Deliverables       | `file-*`                  |
| Signature verified | `seal-check`              |
| Sovereignty        | `globe-simple-x`          |

**Rules:**

- **The logo:** construction comes from it (true 30° angles, cube spacing, its axes and easing curves), but no glyph contains the logo, its ring of cubes, its star core or its cut-outs.
- **Shapes:**
  - The hexagon _cell_ is only for rule verdicts and the pack and skill cubes. The ring is for run and person state. The cell is never a generic container or a rail node.
  - Dashes always and only mean "not established".
- **Colour:**
  - `currentColor` only; colour comes from a token on the wrapper.
  - Every verdict glyph is paired with its word.
- **Banned Phosphor glyphs:** `cube`, `package`, `hexagon` and `link`, because owned glyphs carry those meanings. `check-circle` and its siblings are never used for rule verdicts.
- **Motion:** only on a state change seen live. It plays once for 120–600 ms, as a stroke drawing in or a move along the logo's axes. The only loop allowed is a slow opacity breathe of at least 2.4 s while something is running. Reduced motion shows the final frame.
- **No glass:** no translucency beyond the flat 0.2 duotone tint. No blur, gradients, highlights, shadows, bevels or shaded cube faces.
- **The generator** (`tools/icons`, run as `just icons`) builds every icon component. It rejects any filter, gradient, mask, transform or opacity other than 0.2, and draws a contact sheet at 16, 20, 24 and 32 px next to Phosphor neighbours.
- **Before adoption:** the hexagon verdict badges, the `rule` glyph and the 16 px `skill` glyph are previewed in the real app. Phosphor's circle icons are the fallback for verdicts.

## Checks

- **Design lint** rejects:
  - raw palette classes
  - arbitrary values
  - hex colours outside the token files
  - `backdrop-filter`
  - scaling above 1
- **Contrast test:** every text token on every surface token.
- **axe** on every route.
- **Playwright snapshots** of `/ui` and the pitch-demo screens in light, dark, reduced motion, Hindi and print.
