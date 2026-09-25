---
title: Workbooks, decks and calculations with every step shown
type: git-history
status: historical
date: 2026-09-24
commits: [7d5e304, 11f9ac1]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
---

# Workbooks, decks and calculations with every step shown

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `7d5e304` | 2026-09-24 | Yash Kumar Singh | Deliver workbooks and decks, and ground them in the request's readings |
| `11f9ac1` | 2026-09-24 | Yash Kumar Singh | Work calculations in code, with every step shown |

## Summary

The problem statement asks for PowerPoint, Word and Excel deliverables, and for
calculations with the steps shown. 4CE produced only `.docx`, and did no
engineering arithmetic in code apart from the SOP comparison.

## Why it changed

Those two requirements. Testing the workbook path also exposed the chain
answering the wrong question, for reasons that had nothing to do with files
(below).

## Files changed

- `4ce/tools/deliverables.py` (`create_spreadsheet`, `create_presentation`)
- `4ce/tools/calculations.py` (new, 298 lines)
- `4ce/tools/sop_check.py`, `4ce/functions/orchestrator.py`, `4ce/install.py`, `4ce/preflight.py`, `4ce/test_tools.py`
- `src/lib/components/chat/Messages/Markdown/FileCard.svelte`
- `README.md`, `4ce/README.md`, `4ce/docs/*`

## Technical changes

- **Workbooks** (`7d5e304`). A sheet per table, numbers stored as numbers,
  units moved into headers, and a stated total turned into a live `SUM` only
  after it is checked to add up. The SOP rule pack's verdict table is appended
  verbatim.
- **Decks** (`7d5e304`). A 16:9 `.pptx` with a key-message slide, a slide per
  section, native table slides, speaker notes, and a closing "How this was
  produced" slide.
- **Readings assessed once, from the request** (`7d5e304`). Before this, the
  rule pack also took numbers from FRIDAY's quotes of the sample report, and
  gave different verdicts on each try. FRIDAY now reasons from the verdicts,
  and treats the requester's readings as data.
- **Vibration velocity** (`7d5e304`). Reported as given but not assessed,
  because SOP-MEC-014 states vibration as ISO 10816 zones that depend on the
  machine class.
- **Calculations** (`11f9ac1`). Corrosion rate, remaining life and next
  inspection, from a sentence or a thickness-survey table, with each step and
  unit written out. It reproduces the worked example: 0.267 mm/year, 6.4
  years. In a workbook it is a sheet of live formulas.
- **SOP §4.2 in the calculation** (`11f9ac1`). The rule pack read only
  "measured" and "retirement" thickness, so a 1.7 mm margin slipped past the
  six-month rule. It now also reads "current" and "required", and the
  interval the SOP requires caps the next inspection: 6 months, not 3.2 years.

## Impact

`install.py` registers a fifth tool, and preflight counts five.

## Related documentation

- [DEMO_SCRIPT.md - P4b and P6](../DEMO_SCRIPT.md#p4b--a-calculation-with-every-step-shown)
- [ADR-0004](../decisions/0004-deterministic-tools-for-arithmetic.md)
- [Timeline](README.md)
