---
title: Motion language
type: adr
status: planned
owner: R3
updated: 2026-11-12
covers:
  - apps/web/src/lib/ui/
tags: [4ce, adr, frontend]
number: 42
decision_status: proposed
superseded_by: null
---

# ADR-0042: Motion language

## Context

[ADR-0041](0041-exact-match-look.md) fixed the look of `apps/web` to the running app, and [the design system page](../architecture/design-system.md) keeps motion calm: named durations, no overshoot, no springs, no blur.

On 2026-11-11 the frontend owner reviewed the rebuilt app and found that it does not feel finished. Most state changes are instant: a provenance row pops open, a Settings tab swaps, a hover snaps on and off. The owner asked for one motion language across the app, in the current visual style, and accepted a gentle spring when asked.

Two of the asks conflict with the written rules: a spring overshoots, and the rules say none may.

## Decision

### 1. One arrival curve for interactive surfaces

`--ease-expo`, `cubic-bezier(0.16, 1, 0.3, 1)`, is the curve for things the user moves directly: a sliding highlight, an opening row, a menu. It starts fast and settles slowly, so the interface answers at once and comes to rest quietly. `--ease-out` stays for content arriving on its own.

### 2. One spring, for position only

`--ease-spring` is a single `linear()` curve that overshoots by at most 3 % and settles at 1. It may time a highlight sliding between two resting places, and nothing else. It never times scale, opacity, size or colour. This replaces "No overshoot and no springs" with "one spring, for position, at most 3 %". Every other curve still stays within 0 to 1.

### 3. Hover and press

**Amended 2026-11-12.** Hover, press and focus change in `interact`, 150 ms, on `--ease-standard`, `cubic-bezier(0.4, 0, 0.2, 1)`, the same in and out. This is what the running app measures. The first version, in at `instant` and out at `base` on `--ease-out`, held every hover for 240 ms on the way out, and the owner found it laggy beside the running app.

- **100 ms** (`instant`) where the running app uses 100 ms, such as the sidebar's section headings.
- **Panels, dialogs and page moves** keep `base` or longer.
- **Lift and shadow on hover** are allowed where the running app has them: a card may rise 1 px, darken its border and gain the running app's soft shadow, in 200 ms.
- **Press:** a pressed control scales to 0.96, the existing lower limit.

### 4. Menus grow from their trigger

A menu scales from 0.96 at the edge nearest its trigger, in `menu` on `--ease-expo`.

### 5. A new signature motion: the wire draw

An opened provenance row draws an ink rule from left to right, in `slow` on `--ease-expo`. It is the stage rail's finished wire, reused. It joins the signature motions.

### 6. Routes crossfade

Moving between routes crossfades the page with the browser's view transitions where they exist. The sidebar stays still.

### 7. What stays

No blur in transitions. No rotation, with one exception (amended 2026-11-12): the logo mark turns 120° when its card is hovered, as in the running app, in 700 ms on that app's curve, which overshoots slightly. The mark is rotated, never redrawn. No element scales above 1 or below 0.96. Expand and collapse animate `grid-template-rows`. Under reduced motion nothing moves or scales, the spring is not used, and crossfades take 120 ms or less.

## Alternatives considered

- **Keep the rules as they are.** The motion would be consistent but the owner's finding stands: with no settle, a sliding highlight reads as mechanical.
- **Springs everywhere.** Lively, but it breaks "calm motion" and makes scale exceed 1.
- **A motion library.** Not needed: CSS `linear()`, transitions and view transitions cover every case, and no package is added.

## Consequences

- The design system page's motion rules change as above.
- `motion.test.ts` checks that the interaction rule in `app.css` uses `interact` on the standard curve, with no slower leave.
- `motion.test.ts` gains a check that the spring peaks at 1.03 or less and ends at 1. The existing check that fades never overshoot stays.
- Browsers without `linear()` or view transitions fall back to `--ease-expo` and to an instant route change.

## Status

Proposed. The frontend owner accepts it by merging the pull request that carries it.
