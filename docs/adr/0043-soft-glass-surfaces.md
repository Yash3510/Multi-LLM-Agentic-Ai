---
title: Soft glass surfaces
type: adr
status: planned
owner: R3
updated: 2026-11-12
covers:
  - apps/web/src/lib/ui/
tags: [4ce, adr, frontend]
number: 43
decision_status: proposed
superseded_by: null
---

# ADR-0043: Soft glass surfaces

## Context

[The design system page](../architecture/design-system.md) says surfaces are "opaque and flat": no glass, blur, sheen or gloss. [ADR-0042](0042-motion-language.md) kept that.

On 2026-11-12 the frontend owner reviewed the details under an answer (five separate rows: full provenance, two agent outputs, the execution timeline and the sources) and asked for one clearer panel, with softer and rounder shapes and a glass finish, across the whole app. The owner also saw a version with violet timeline marks and a violet glow behind the panel, and rejected both.

The glass finish conflicts with the written rule.

## Decision

### 1. One details panel under an answer

The five rows become one panel with four tabs: Provenance, Reasoning, Timeline and Sources. The labels, the "What was checked" card and the stage rail stay as they are. The panel shows only what the run recorded; it invents no figure, passage or count.

### 2. Glass, for surfaces that float

A surface that sits over other content (a menu, a popover, a dialog, the composer, the top bar) may be glass: a fill at 72 to 86 % of its surface colour, `backdrop-filter: blur(20px) saturate(1.4)`, a one-pixel top highlight and its existing shadow level. The values live in the `--glass-*` tokens and the `glass` rule in `tokens/glass.css`; no component writes its own.

A surface in the flow of the page has nothing behind it to blur. It takes the soft fill and the highlight only.

This replaces "No glass, blur, sheen or gloss" with "glass for floating surfaces, from the glass tokens only".

### 3. Rounder shapes

`inset` goes from 12 to 14 and `panel` from 20 to 24. The details panel uses `panel`; its tabs and reference marks are pills. The nesting rule stays: an inner radius is the outer radius minus the padding between them.

### 4. No violet and no glow

Violet keeps its one meaning: an agent is working, or keyboard focus. The timeline's marks are ink nodes on a hairline wire. No surface has a coloured glow, wash or gradient behind it.

### 5. What stays

Text contrast is measured against the surface colour a glass fill falls back to, and still meets AA. Where `backdrop-filter` is missing, or the person asks for reduced transparency, the fill is opaque. Transitions still use no blur.

## Alternatives considered

- **Keep surfaces opaque.** Consistent with the written rule, but the owner asked for the glass finish after seeing both.
- **Glass on every card.** A card in the flow has nothing behind it, so the blur costs paint time and shows nothing.
- **Violet marks on the timeline.** It would give violet a second meaning, and the owner rejected the look.

## Consequences

- The design system page's depth and radius rules change as above.
- Blur costs paint time on large surfaces; it is limited to floating ones.
- `details.test.ts` covers how the run's record maps to the four tabs.

## Status

Proposed. The frontend owner accepts it by merging the pull request that carries it.
