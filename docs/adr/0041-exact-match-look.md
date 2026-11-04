---
title: Exact-match look
type: adr
status: planned
owner: R3
updated: 2026-11-03
covers:
  - apps/web/src/lib/ui/
  - tools/design-lint/
tags: [4ce, adr, frontend]
number: 41
decision_status: proposed
superseded_by: null
---

# ADR-0041: Exact-match look

## Context

[ADR-0035](0035-frontend-foundations.md) set a new visual language for `apps/web`: an owned graphite and violet palette, eight type steps, opaque surfaces only, and a design lint that enforces them. The values are in [the design system page](../architecture/design-system.md).

On 2026-11-03 the frontend owner compared the running 4CE chat app with two mocks of the new language and chose to keep the current look. The new app must be a pixel-exact replica of today's app: at least 98 % identical pixels per screen, checked side by side against the running app. It is still written as new code, from behaviour specs and measured style tables, never from the old source.

The measured look does not fit ADR-0035's rules. It uses:

- a neutral grey ramp and stock palette colours (blue, sky, red, green, amber and others)
- muted text below 4.5:1 (for example #9b9b9b on white)
- type from 9 px to 30 px
- backdrop blur and translucent white surfaces
- a 1.25 scale pulse

## Decision

### 1. The look is measured, not designed

The visual source of truth is the measured style tables (`look.md` per area, kept outside the repository with the behaviour specs) and the running app. Where the two disagree, the running app wins, and the table is corrected.

### 2. Tokens

- **The measured ramp is the primitive tier.** Grey 50 to 950 (#f8f8f8 to #0d0d0d), white and black, and the palette colours the tables use, under the names the tables use (`gray-500`, `blue-500`, `sky-500` and so on). Builders transcribe a table directly.
- **The semantic roles stay as aliases** onto the ramp (surface, line, ink, accent, verdicts), so existing components keep working while they are restyled.
- **The type, radius, shadow and spacing scales are the framework defaults** the tables are written in (Tailwind 4: text-xs to text-3xl, radius sm to 3xl, the default shadows and the 4 px spacing unit), plus the named odd sizes the tables use (13 px sidebar text, 15 px answer text and the rest).
- **Themes are light, dark and OLED dark.** Dark keeps the root `data-theme` marker, and the `dark:` variant keys off it, so the tables' dark classes work unchanged. OLED dark overrides four greys (800, 850, 900, 950); it is planned, not built yet.

### 3. Checks follow the look

- **The design lint is retuned.** It keeps rejecting hex colours and arbitrary values outside the token files, and drop-shadow filters. It allows blur, backdrop blur, translucent surfaces, `dark:` variants, palette classes and the 1.25 pulse, because the measured look uses them.
- **The contrast test checks the measured pairs** instead of ADR-0035's 4.5:1 tiers. It still fails when a token drifts from its measured value.
- **The pixel check is the new gate.** Each screen is compared with the running app and its identical-pixel share reported.

### 4. What stays from ADR-0035

Stack, serving, live updates, API contract, roles and labels, devices, languages, keyboard access, Phosphor icons (the measured app uses Phosphor too) and the clean-room rule. The six role names stay; the upstream product's name never appears.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Keep ADR-0035's visual language | The owner chose the current look after a side-by-side comparison. |
| Exact match, semantic roles only | Every grey in the tables would need translating into a role by hand, and each translation is a chance to drift. |
| Exact match, checks unchanged | Blur, translucency and sub-11 px type would be impossible, so screens could not reach 98 %. |

## Consequences

- ADR-0035 §8 (theme mechanism), §9 (contrast tiers only; keyboard and screen-reader rules stay), §10 (values), §11 (no glass), §12 (icons: the running app's Phosphor glyphs and weights per place, see the amendment) and the design-lint part of §13 are superseded.
- [design-system.md](../architecture/design-system.md) describes the superseded language and must be rewritten to point at the measured tables and these tokens.
- Muted text below 4.5:1 returns. Accessibility mode, which the measured app has, raises it, and must be rebuilt.
- The grey ramp's values match the upstream project's. They are measured colour values, not copied files, so the clean-room rule still holds. If R4 disagrees, they can say so before acceptance.

## Amendment, 2026-11-03: premium base components

After reviewing the first restyle side by side, the frontend owner rejected three things: the icons, the outlines round the pills, and the full-pill curve. Following an approved preview, the base components (actions, fields, status and the `/ui` reference) now deviate from the exact match:

- **Icons are Phosphor, as the running app draws them** (2026-11-04, replacing the Lucide set chosen earlier in this amendment). Glyphs come from `@phosphor-icons/core` 2.1.1 (MIT), filled paths on the 256 grid. `tools/icons` maps each of our names to the glyph and weight the running app uses in that place. Glyphs were identified by matching the app's rendered paths against the package, not by copying its code. Most places are regular; the row "more" dots, select and picker carets, the back caret, minus and the send arrow are bold where the app draws them bold. 4CE concepts the app does not show use the closest regular glyph: verdicts are check-circle, warning, x-circle and circle-dashed. Sizes and colours are the running app's (16 px in the sidebar and rows).
- **The running app is the only reference** (2026-11-04). Wherever the premium pass above differs from the running app, the running app wins; only the Phosphor icon set stays from the premium pass. Screens are matched one at a time, and each component returns to the measured look when its screen is matched (the shell, menus and conversation so far).
- **The licence notice ships with the glyphs.** `tools/icons` writes the package's MIT licence as a `/*! @license … */` comment on the generated path table, and `vite.config.ts` keeps legal comments through minification (Vite 8 drops them by default). There is no copied licence file in the source tree.
- **Menus match the running app exactly** (common look F12), not the premium float: a 1 px line-1 border, 12 px radius, 2 px padding, the large soft drop shadow and ink text. Rows are 27 px, 12 px radius, 8 px sides and gap, 13 px text and 14 px icons. The hover is gray-50 at 60 % (gray-800 at 60 % dark), and dividers are gray-50 at 30 % with a 2 px by 4 px margin. A destructive row reads like the others, as the app's Delete does. The keyboard highlight keeps the soft blue inner edge, because the app shows no visible focus there.
- **The logomark is the owner's brand-kit file**, used unchanged: `4ce-logomark-ink.svg` on light grounds and `4ce-logomark-white.svg` on dark, at 22 px in the sidebar header and rail.
- **The splash may name token values in `app.html`** (2026-11-05). The splash paints before any stylesheet loads, so it can't use a token. The design lint therefore lets `app.html` (and only that file) use a hex colour when a token file holds exactly that value, compared without regard to case. Any other hex there still fails, and `tools/design-lint` tests both cases. The splash ground is `--ref-white` on light and `--ref-gray-900` on dark, and the mark is the brand-kit file, served unchanged from `static/brand/`.
- **Shape:** buttons are 10 px soft rectangles, fields and menus 12 px, cards and dialogs 20 px. Full pills are kept for status chips only.
- **Depth without borders:** a 0.5 px hairline ring plus soft contact and ambient shadows. The solid button gets a faint inner highlight, and a press settles it to 98%.
- **Focus** is a soft blue glow outside the shape, never a hard ring. Forced-colours mode falls back to a system outline.
- **Choices:** segmented controls use a raised thumb that slides on a faint track, and check boxes are 16 px with a solid fill when checked.

The idea for the tactile depth came from the owner's own Takeoff project. Its values were rewritten here, not copied. Screens built later still follow the measured tables for layout, sizes and colours, and use these components. The pixel check therefore measures screens with these components as the baseline.

## Status

Proposed on 2026-11-03 by the frontend owner. To be accepted by:

- the frontend owner: accepted on 2026-11-03
- R1, as owner of ADR-0035's shared parts: pending
