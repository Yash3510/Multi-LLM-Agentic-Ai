---
title: Grounding the chain, and holding citations to the documents
type: git-history
status: historical
date: 2026-09-18
commits: [09cc868, e1a0682, 2b0d6c9]
authors: [Yash Kumar Singh]
tags:
  - 4ce
  - git-history
  - agent
---

# Grounding the chain, and holding citations to the documents

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `09cc868` | 2026-09-18 | Yash Kumar Singh | Retrieve for the chain, instead of assuming the platform's grounding survives |
| `e1a0682` | 2026-09-19 | Yash Kumar Singh | Ground the chain on the knowledge base that was attached all along |
| `2b0d6c9` | 2026-09-24 | Yash Kumar Singh | Hold citations to what the documents say, and measure it |

## Summary

Local RAG was listed as verified, but its passages never reached the agents.
The chain now retrieves for itself, reports how much grounding actually
arrived, filters out irrelevant passages, and fails an answer that attributes
an invented figure to the SOP.

## Why it changed

- The platform grounds an ordinary model by rewriting its system message. Each
  agent here has its own system prompt, so the retrieved passages were
  discarded before FRIDAY saw them (`09cc868`).
- Even then, retrieval returned nothing. The platform only includes a model's
  knowledge base under legacy function calling, which a pipe does not use. The
  provenance row hid this by counting a constant 148 characters of platform
  preamble as grounding (`e1a0682`).
- Vector search always returns its nearest chunks: "What is the capital of
  France?" retrieved the seal leakage SOP at 0.68 similarity (`2b0d6c9`).

## Files changed

- `4ce/functions/orchestrator.py`
- `4ce/eval_retrieval.py` (new, `2b0d6c9`)
- `4ce/test_tools.py`, `4ce/docs/HOW_TO_RUN.md`, `4ce/docs/SETUP_MACOS.md`, `4ce/README.md`

## Technical changes

- **Retrieval inside the chain** (`09cc868`). Queried against the collections
  attached to the request and handed to FRIDAY. A new provenance row reports
  how much context reached FRIDAY.
- **Knowledge base from the model record** (`e1a0682`), not from the request's
  `files`. Retrieval runs after classification, so greetings and code
  requests are not padded with plant procedures. The grounding row counts only
  retrieved passages and says "none" when there were none.
- **Token usage recorded** (`e1a0682`). Usage and analytics had reported zero
  for a system running four models.
- **Relevance guard** (`2b0d6c9`), ported from the first prototype. A passage is
  kept only if it shares a word of substance with the request, or its
  similarity is at least 0.8.
- **No citation, no claim** (`2b0d6c9`). A figure attributed to the SOP that no
  passage, reading, rule pack or calculation contains fails the answer.
- **Not found is an answer** (`2b0d6c9`). When nothing relevant survives, FRIDAY
  says the plant documents do not cover the question.

## Impact

The same seal-leakage question now quotes clauses 2.1 and 2.2 verbatim.
`eval_retrieval.py` measured 15/15 found in the top 4, 13 at rank 1, and 3/3
unrelated questions emptied by the guard ([TESTING.md](../TESTING.md)).

## Related documentation

- [AGENT_CHAIN.md - deterministic steps](../AGENT_CHAIN.md#deterministic-steps---before-any-agent)
- [Timeline](README.md)
