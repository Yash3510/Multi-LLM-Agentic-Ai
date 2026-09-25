---
title: Development timeline
type: git-history
status: active
updated: 2026-09-25
last_processed_commit: 195cb9f
tags:
  - 4ce
  - git-history
---

# Development timeline

How 4CE was built, milestone by milestone, from the repository's history. Each
page lists its commits and was written from their diffs, not only their
messages. Every commit is in exactly one milestone.

**Last processed commit:** `195cb9f` (2026-09-25). The next maintenance pass
starts after it: `git log 195cb9f..HEAD`.

For a shorter, user-facing summary by date, see [CHANGELOG.md](../CHANGELOG.md).

---

## 2026-09-08 - Foundation

| Milestone | Commits | What it established |
|---|---|---|
| [Foundation](2026-09-08-foundation.md) | 5 | The agent chain as a pipe function; the sandbox, Word and sovereignty tools; the installer; the air-gapped configuration |
| [Visible reasoning and a fail-closed approval gate](2026-09-08-visible-reasoning-and-approval-gate.md) | 4 | Per-agent reasoning blocks, `<think>` kept out of deliverables, the provenance table, typed APPROVE |
| [Per-agent models, bounded turns and the conversational fast path](2026-09-08-per-agent-models-and-fast-path.md) | 4 | Per-agent model valves, the first test suite, image and reply bounds, greetings answered directly |
| [Repository layout, licence and public documents](2026-09-08-repository-licence-and-docs.md) | 16 | 4CE README, `4ce/docs/`, SECURITY and CONTRIBUTING, vault settings; the licence removed and restored |

## 2026-09-10 to 2026-09-15 - Identity and surface

| Milestone | Commits | What it established |
|---|---|---|
| [Branding, the first-run screen and the static assets](2026-09-10-branding-and-first-run.md) | 7 | The 4CE mark generated from source everywhere, the industrial first-run screen, the static-directory fix |
| [Withdrawing the surfaces that could leave the premises](2026-09-11-surface-reduction.md) | 10 | Integrations, web fetch, browser speech and Gravatar withdrawn; third-party endpoints blanked; audit from 11 to 18 checks |
| [The SOP threshold checker](2026-09-13-sop-threshold-checker.md) | 1 | Clause-cited verdicts from an authored rule pack |

## 2026-09-18 to 2026-09-20 - Making the claims true

| Milestone | Commits | What it established |
|---|---|---|
| [The chain uses its tools, executes its code and returns typed files](2026-09-18-tool-using-chain.md) | 9 | Tools connected, verification on a different model, all code executed, typed artefacts, honest stop and failure reporting |
| [Grounding the chain, and holding citations to the documents](2026-09-18-grounding-and-citations.md) | 3 | Retrieval inside the chain, a truthful grounding row, the relevance guard, "no citation, no claim" |
| [Preflight, runbooks and build reliability](2026-09-18-preflight-runbooks-and-build.md) | 14 | `preflight.py`, the demo script, the macOS guide, a rebuildable knowledge base, build fixes |

## 2026-09-22 to 2026-09-23 - The interface

| Milestone | Commits | What it established |
|---|---|---|
| [The live chain interface](2026-09-22-live-chain-interface.md) | 22 | Stage rail, overview tree, intro and mark motion, failure card, trust view, sidebar outcome marks |
| [Evidence, fingerprints and the sign-off review](2026-09-22-evidence-and-sign-off.md) | 10 | Numbered sources, figure check, SHA-256 fingerprints, "what changed on try 2", the audit sheet, sign-off reconnection |

## 2026-09-24 to 2026-09-25 - Against the problem statement

| Milestone | Commits | What it established |
|---|---|---|
| [Observed egress and the Sovereignty page](2026-09-24-observed-egress.md) | 1 | The egress watch, the canary, per-run external counts |
| [Closing the verification loop on what actually ran](2026-09-24-execution-verification-loop.md) | 1 | The sandbox result as 4CE's own check; passes with reservations |
| [Workbooks, decks and calculations with every step shown](2026-09-24-workbooks-decks-and-calculations.md) | 2 | `.xlsx` and `.pptx` deliverables; remaining-life calculations in code |
| [Routing by a model registry](2026-09-24-model-registry.md) | 1 | `models.json` as the one list the router, picker and preflight read |
| [Reading scans, handwriting and drawings into checkable fields](2026-09-25-reading-images-into-fields.md) | 1 | The image reading pass, boxed fields, `eval_vision.py`, the verdict check |

---

## Contributors

| Author | Commits | Main areas |
|---|---|---|
| Yash Kumar Singh | 65 | Orchestrator, tools, installer, preflight, egress watch, docs |
| Pranay Harish Munj | 33 | Interface, evidence and sign-off, Word report style |
| rituraj thakur | 7 | README edits, licence file |
| grizzly077 | 6 | SOP threshold checker, run guide, interface naming, withdrawn settings |

Counts are from `git shortlog -sn` at `195cb9f`.

---

## Maintaining this page

When new commits land:

1. `git log --reverse <last_processed_commit>..HEAD` to list them.
2. Add each commit to one milestone: an existing one if it continues that
   work, otherwise a new page named `YYYY-MM-DD-short-title.md`.
3. Update the table above, the contributor counts, `last_processed_commit`,
   and [CHANGELOG.md](../CHANGELOG.md).
4. Update any page in [../](../README.md) whose subject the commits changed.
