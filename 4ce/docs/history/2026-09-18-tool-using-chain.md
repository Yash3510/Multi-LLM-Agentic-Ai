---
title: The chain uses its tools, executes its code and returns typed files
type: git-history
status: historical
date: 2026-09-18
commits: [fef00fe, 327e143, 04173c1, 2e254d8, 59bfcb3, d7cfde5, 1854bb0, 4731bb5, cef4459]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - agent
---

# The chain uses its tools, executes its code and returns typed files

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `fef00fe` | 2026-09-18 | Yash Kumar Singh | Let the agent chain use the tools it ships with |
| `327e143` | 2026-09-18 | Yash Kumar Singh | Run every code block the model wrote, not just the first |
| `04173c1` | 2026-09-18 | Yash Kumar Singh | Return the artefact the request asked for, in the type it asked for |
| `2e254d8` | 2026-09-18 | Yash Kumar Singh | Recognise code the model forgot to fence |
| `59bfcb3` | 2026-09-18 | Yash Kumar Singh | Stop the greeting reciting agent names it cannot spell |
| `d7cfde5` | 2026-09-19 | Yash Kumar Singh | Report what the run actually did, not what it was asked |
| `1854bb0` | 2026-09-20 | Yash Kumar Singh | Account for a run the reviewer stopped |
| `4731bb5` | 2026-09-20 | Yash Kumar Singh | Let a throwaway remark stay a throwaway remark |
| `cef4459` | 2026-09-20 | Yash Kumar Singh | Say why the model refused, instead of "empty response" |

## Summary

The tools had been installed and tested but never connected to the chain.
This milestone connected them, so the chain measures where it had been
reasoning. It also executes all the code it writes, returns files in the type
the request asked for, and reports honestly on runs that were stopped or that
failed.

## Why it changed

Testing against a real inspection prompt showed the agents reasoning where
they should have been measuring (`fef00fe`):

- The tools were unreachable. `pipe()` did not declare `__tools__`, and nothing
  attached the tools to the orchestrator's model.
- ULTRON read a 6.2 mm wall against a 6.0 mm limit as a breach, forced a
  replan on that false premise, and released nothing after 130 seconds.
- ULTRON ran on the same weights as JARVIS.
- A stopped run left an endless spinner, and after a reload the reply was gone.

## Files changed

- `4ce/functions/orchestrator.py`
- `4ce/install.py` (attaches the tools)
- `4ce/tools/sandbox.py`, `4ce/tools/deliverables.py`, `4ce/test_tools.py` (`04173c1`)
- `4ce/docs/HOW_TO_RUN.md` (`327e143`)

## Technical changes

- **Tools connected** (`fef00fe`). The installer writes the tool ids onto the
  model. Threshold comparisons go to `sop_check`, code runs before it is shown,
  an audit reads the live configuration, and an approved document becomes a
  `.docx`. Which tools ran is recorded in the provenance table. The same
  prompt then passed first time in 50 s, with the clause cited and the wall
  read the right way round.
- **Independent verification by default** (`fef00fe`). A blank ULTRON valve
  crosses to a different served model
  ([ADR-0003](../decisions/0003-verify-on-a-different-model.md)).
- **Cancellation** (`fef00fe`, `1854bb0`). The chain runs in an inner method so
  `pipe()` can catch a stop, close the bubble, write the turn and record the
  tokens already spent. It also moved the status line to "Stopped by reviewer".
- **Every code block** (`327e143`). Blocks are joined in order, and interpreter
  transcripts and shell lines are skipped. The median example then ran and
  returned 5.
- **Unfenced code** (`2e254d8`). The Python parser recovers the longest run of
  leading lines that parses as a program; prose returns nothing.
- **Typed artefacts** (`04173c1`). A writable `/output` mount per run is read
  back and registered for download, and the container never sees the
  operator's directory. Each fenced block becomes a typed file, restricted to
  ordinary text types. Nothing is written until approval.
- **Honest reporting** (`d7cfde5`). The SOP rule pack runs only when the
  request carries readings. The reviewer's waiting time is excluded from
  elapsed time. Files are named after what they contain.
- **Conversation** (`59bfcb3`, `d7cfde5`, `4731bb5`). A greeting gets a
  greeting, without the agent roster the small model misspelled. Courtesies
  such as "and again" stay out of the chain.
- **Refusals** (`cef4459`). A context overflow now reports the server's own
  sentence, "request (10258 tokens) exceeds the available context size (8192
  tokens)", instead of "empty response", and the status line is closed on
  failure paths.

## Impact

This is the point where the chain's claims (grounded thresholds, executed code,
typed deliverables) became true in practice rather than in principle.

## Related documentation

- [AGENT_CHAIN.md](../AGENT_CHAIN.md)
- [ADR-0004](../decisions/0004-deterministic-tools-for-arithmetic.md)
- [Timeline](README.md)
