---
title: Closing the verification loop on what actually ran
type: git-history
status: historical
date: 2026-09-24
commits: [8559acc]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - agent
---

# Closing the verification loop on what actually ran

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `8559acc` | 2026-09-24 | Yash Kumar Singh | Close the verification loop on what actually ran |

## Summary

The sandbox's result became 4CE's own check, ahead of ULTRON's. A pass that
comes with objections now says so, and a list written in prose is no longer
mistaken for citations.

## Why it changed

Three faults were seen in live runs:

- ULTRON passed results while listing problems beneath them, and the chat
  showed a green pass over "a problem".
- Generated code was run, but nothing acted on the result, so a crash could
  pass if the verifier missed it.
- "the median of [5, 3, 9, 1, 7]" was read as five citations to sources that
  did not exist.

## Files changed

- `4ce/functions/orchestrator.py`, `4ce/test_tools.py`
- `src/lib/components/chat/ApprovalPanel.svelte`, `chat/approvalReview.js`, `chat/Messages/Markdown/ReceiptStrip.svelte`
- `src/lib/utils/marked/citation-extension.ts`
- `4ce/docs/DEMO_SCRIPT.md`

## Technical changes

- **Execution check.** A non-zero exit, a timeout, a missing code block, or a
  program asked to print that printed nothing fails the result and sends it
  back once with the real error. Code that could not be run is unverified and
  final. A clean run that asserts nothing reads *could not check*, and JARVIS
  is asked to assert its own result.
- **Reservations.** ULTRON's verdict word still decides, but a pass with
  objections reads "with N reservations", in amber, everywhere the verdict is
  shown.
- **Citation syntax.** A citation is one to four source numbers in ascending
  order, with the same rule in the orchestrator and the chat's citation chips.
  Anything else in square brackets is data.

## Impact

On the median prompt: try 1 dropped the function's result and claimed
"Output: Median: 5.0". 4CE failed it for printing nothing, try 2 printed 5,
and ULTRON cited the sandbox output in passing it.

## Related documentation

- [AGENT_CHAIN.md - ULTRON](../AGENT_CHAIN.md#ultron---challenge)
- [ADR-0004](../decisions/0004-deterministic-tools-for-arithmetic.md)
- [Timeline](README.md)
