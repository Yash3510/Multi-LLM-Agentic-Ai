---
title: Evidence, fingerprints and the sign-off review
type: git-history
status: historical
date: 2026-09-22
commits: [6ce13f3, dcc2d43, bb6c2f0, b18f785, 080bb60, f2f614f, dca074e, 41cedb1, e8c8163, f276768]
authors: [Pranay Harish Munj]
tags:
  - 4ce
  - git-history
  - agent
---

# Evidence, fingerprints and the sign-off review

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `6ce13f3` | 2026-09-22 | Pranay Harish Munj | Write reports in the 4CE house style, and keep the record honest |
| `dcc2d43` | 2026-09-23 | Pranay Harish Munj | Cite the evidence and show what was checked under every answer |
| `bb6c2f0` | 2026-09-23 | Pranay Harish Munj | Report: sans wordmark and headings, cited sources, readable links |
| `b18f785` | 2026-09-23 | Pranay Harish Munj | Fail on mismatched figures, fingerprint releases, shape every answer |
| `080bb60` | 2026-09-23 | Pranay Harish Munj | Keep the sign-off when the reviewer's tab reconnects |
| `f2f614f` | 2026-09-23 | Pranay Harish Munj | Show the report as a file card; make ULTRON's check lines its own |
| `dca074e` | 2026-09-23 | Pranay Harish Munj | Show what try 2 changed and why; add the audit record |
| `41cedb1` | 2026-09-23 | Pranay Harish Munj | Ink evidence chips, readable labels, fuller report, "waited" for review |
| `e8c8163` | 2026-09-23 | Pranay Harish Munj | Sign-off panel: a review, with hold to release |
| `f276768` | 2026-09-23 | Pranay Harish Munj | Bring back the typed Approve and the two-line suggestions |

## Summary

Every answer now carries its evidence: numbered sources the reader can open,
the checks that were made, what a second try changed, and a SHA-256
fingerprint of the released text. The sign-off became a review of all of that,
and it survives a tab reconnect.

## Why it changed

A reviewer asked to approve an answer needs to see what it rests on. The
record also had to stop misreporting: a sign-off that never reached anyone was
recorded as "rejected by reviewer" (`6ce13f3`).

## Files changed

- `4ce/functions/orchestrator.py`, `4ce/tools/deliverables.py`
- `src/lib/components/chat/ApprovalPanel.svelte`, `chat/approvalReview.js`
- `src/lib/components/chat/Messages/Markdown/` (`ReceiptStrip`, `AuditSheet`, `RevisionCard`, `FileCard`, `Source`, `SourceToken`, `evidence.ts`)
- `backend/open_webui/socket/main.py` (`080bb60`)

## Technical changes

- **Record honesty** (`6ce13f3`). An unanswered sign-off is *not obtained*.
  ULTRON's verdict is read from its first line, or else its last. The approval
  reaches the report tool as `__` parameters that models never see, so only the
  orchestrator can say a person approved a document.
- **Word report house style** (`6ce13f3`, `bb6c2f0`, `41cedb1`). Masthead,
  classification, metadata panel, verification record, release statement,
  raised citations with a Sources list, and the clauses behind each cited
  figure.
- **Numbered sources** (`dcc2d43`). FRIDAY and JARVIS cite `[n]`. Each `[n]`
  is a chip that opens the exact passage. A number that names no retrieved
  document is dropped, and the claim is marked *(unverified)*. A receipt line
  sits above a folded provenance table.
- **Figure check and fingerprint** (`b18f785`). A figure cited to a document
  that lacks it fails the answer whatever ULTRON said. ULTRON runs with
  `/no_think`. A tidy pass removes clutter before verification. Released text
  gets a SHA-256 fingerprint, shown on the receipt and in the report.
- **ULTRON's own check lines** (`f2f614f`). The example lines in its prompt were
  removed, because the small verifier copied them verbatim. Over six samples
  it then passed consistently.
- **What changed on try 2** (`dca074e`). The drafts are compared sentence by
  sentence and each objection matched to its changes. An audit sheet records
  the steps, sources and fingerprint, with a box that verifies a pasted copy.
- **Sign-off reconnect** (`080bb60`). A pending sign-off is re-sent to the same
  user's live sessions after a reload. Tested: the panel was back in under
  5 s.
- **Sign-off panel** (`e8c8163`, `f276768`). The panel shows the draft beside
  its checks and sources. Hold-to-release was tried, then replaced by the
  typed `approve` again.

## Impact

These are the evidence and audit claims made in the demo. See
[ADR-0002](../decisions/0002-fail-closed-human-approval.md) and
[ADR-0004](../decisions/0004-deterministic-tools-for-arithmetic.md).

## Related documentation

- [AGENT_CHAIN.md - ULTRON](../AGENT_CHAIN.md#ultron---challenge)
- [Timeline](README.md)
