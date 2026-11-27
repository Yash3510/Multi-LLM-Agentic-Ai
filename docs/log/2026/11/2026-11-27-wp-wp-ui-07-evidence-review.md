---
title: "apps/web: evidence review"
type: log
status: implemented
owner: R3
updated: 2026-11-27
date: 2026-11-27
branch: wp/WP-UI-07-evidence-review
pr: 14
work_package: WP-UI-07
author: Pranay Munj
areas: [apps/web]
tags: [4ce, log, frontend]
---

# apps/web: evidence review

## What changed

- **Evidence in the contract** ([WP-UI-07, part 1](../../../architecture/frontend.md#wp-ui-07-part-1-evidence-review)): `Evidence` and `Observation`, `getEvidence(id)`, and `Source.evidenceId`. The fake's stored run reads one batch report page into three observations, one of them unsure.
- **The evidence viewer:** the page image with numbered boxes, and the list of what was read, kept in step either way; an unsure observation is boxed dashed and asks for a check.
- **`/evidence/[evidenceId]`:** the viewer with what the evidence was read as and by which model; `?box=` opens on one observation. The run view's Analyst stage links each source with evidence to its review.

## Why

Step 3 of the plan's build order, the first of its four pull requests (web-screens.md, evidence review).

## Files

| Path | Change |
| --- | --- |
| `apps/web/src/lib/data/types.ts`, `fake.ts`, `fake.test.ts` | the evidence contract and the fake's page |
| `apps/web/src/lib/ui/components/EvidenceViewer.svelte`, `evidence-viewer.test.ts` | the viewer |
| `apps/web/src/routes/evidence/[evidenceId]/`, `src/routes/runs/[runId]/+page.svelte`, `e2e/evidence.spec.ts` | the page, the link from the run view, the browser tests |
| `docs/architecture/frontend.md`, `web-data-contract.md`, `web-screens.md`, `design-system.md`, `docs/state.md`, `docs/log/README.md` | the docs |

## How it was verified

On macOS (arm64), Node 24.21.0, on this branch (stacked on `wp/WP-UI-03-audit-sheet` at `e5bb11f`). Tests first, each failing before its change:

- `fake.test.ts`, the stored run's evidence: failed, then `src/lib/data/` 83 passed.
- `evidence-viewer.test.ts`: failed (no component), then 2 passed.
- `e2e/evidence.spec.ts`: 2 failed (no route, no link), then with the run view's tests 12 passed on desktop and tablet.

**Every check,** each `just check` recipe run directly (`just` isn't installed here), all exit 0: `lint` 234 files formatted (134 Python, 100 Markdown), pyright 0 errors; `imports` 14 contracts kept; `repo-check` and `neutrality` clean; `docs` exit 0, also with `--base wp/WP-UI-03-audit-sheet`; `licences` 78 components, 114 files, 5 services; `test` 807 passed, 97 deselected; `web-lint` clean, svelte-check 1477 files, 0 errors; `web-test` 96 files, 592 tests, tools 16; `web-e2e` 32 passed.

**Not run:** `just secrets` (gitleaks isn't installed here); the PostgreSQL, Redis and MinIO test sets.

## Decisions

- The fake's page is an SVG drawn in the fake, so the boxes sit exactly on what they read.
- Evidence isn't tied to one run: the documents are shared, so the run view finds evidence through its sources.

## Known limits and follow-ups

- Zoom and pan, page navigation and Verify and Correct come in part 2.
- The fake has one piece of evidence with one page.
