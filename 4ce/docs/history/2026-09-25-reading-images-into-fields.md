---
title: Reading scans, handwriting and drawings into checkable fields
type: git-history
status: historical
date: 2026-09-25
commits: [195cb9f]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - agent
---

# Reading scans, handwriting and drawings into checkable fields

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `195cb9f` | 2026-09-25 | Yash Kumar Singh | Read scans, handwriting and drawings into fields a reviewer can check |

## Summary

An attached image is now read once into numbered fields, each with its unit,
the model's confidence and the box it was read from, before FRIDAY analyses
it. 4CE draws the boxes on a numbered copy, so a reviewer can compare a
doubtful value with its pixels before approving.

## Why it changed

At 900 px, a handwritten log lost a reading on every run and its smudged
figure was never flagged, measured with the new `eval_vision.py`. A figure a
model reads from a page had nothing the reviewer could check it against.

## Files changed

- `4ce/functions/orchestrator.py` (`_read_image`, ISA tag typing, `_reading_checks`, `_verdict_checks`)
- `4ce/eval_vision.py` (new)
- `4ce/demo/make_samples.py`; new samples `shift_log_P-101.png` and `pid_P-101_excerpt.png`, each with an answer key
- `4ce/tools/sop_check.py`, `4ce/tools/deliverables.py`, `4ce/test_tools.py`
- `backend/open_webui/utils/fource_egress.py`, `src/lib/components/fource/Sovereignty.svelte`, `ReceiptStrip.svelte`, `vite.config.ts`
- `4ce/README.md`, `README.md`, `4ce/docs/HOW_TO_RUN.md`, `DEMO_SCRIPT.md`, `SETUP_MACOS.md`

## Technical changes

- **Size by kind.** Pages and drawings go at up to 2200 px
  (`vision_page_edge`), photographs at 900.
- **Reading pass.** Fields are returned as JSON and parsed, with fields kept
  from a reply cut off mid-object. Low-confidence fields are marked **check**.
  P&ID tags are typed from their ISA 5.1 letters.
- **Rule pack.** Readings from a page reach the rule pack as a request's own
  do. A missing guard "bolt" is read, and a defect reported absent ("no
  visible spray") no longer fails.
- **New 4CE check.** An answer that calls a reading within limits fails when
  the rule pack's verdict for it is REVIEW or FAIL.
- **Figure check.** Clock times are skipped, and a true figure given the wrong
  document is shown as mis-cited rather than invented.
- **Smaller fixes.** The platform's attached-files block is stripped from the
  request. A browser opened from the model server's window is no longer
  counted as the model server. The dev server ignores backend, plugin and doc
  edits, which had been reloading the page mid sign-off.

## Impact

The tool suite has 130 checks. `eval_vision.py` at 2200 px: the log complete
and its smudge flagged on 3 of 3 runs, and all 15 P&ID tags read.

## Related documentation

- [AGENT_CHAIN.md - image reading pass](../AGENT_CHAIN.md#image-reading-pass---vision-tasks-only)
- [TESTING.md - vision evaluation](../TESTING.md#vision-evaluation---eval_visionpy)
- [HOW_TO_RUN.md - Reading images](../HOW_TO_RUN.md#reading-images)
- [Timeline](README.md)
