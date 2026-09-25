---
title: "ADR-0008: Answer conversation directly"
type: decision
status: accepted
updated: 2026-09-25
tags:
  - 4ce
  - decision
  - agent
---

# ADR-0008: Answer conversation directly

## Context

Typing "hello" ran FRIDAY, JARVIS and ULTRON, then asked a person to type
APPROVE before releasing the greeting. That wasted about a minute and devalued
the approval gate: a reviewer trained to approve greetings will approve
anything (`abbcab7`).

## Decision

TONY recognises messages that are entirely social or about the assistant, 8
words or fewer, and answers them directly on the chat model. There are no
agents, no verification and no approval gate. The match is strict: anything
that looks like work still gets the full chain. "hello" is conversation;
"hello, draft an approval note for pump P-101B" is a document task.

The `orchestrate_small_talk` valve sends conversation through the full chain
instead. It is off by default.

## Alternatives considered

- **Orchestrate everything.** This was the original behaviour, described above.

## Consequences

- A greeting answers in seconds and shows `direct reply · qwen3-1.7b · no agent
  chain` in its footer, which makes the cost of the chain on real work read as
  deliberate ([DEMO_SCRIPT.md - P1](../DEMO_SCRIPT.md#p1--it-knows-when-not-to-be-an-agent)).
- The word lists need tending. "and again" was classified as work until
  courtesies were added (`4731bb5`).
- The small model misspelled the agent names when it recited them, so a
  greeting now gets a greeting, and the names are pinned for when they are
  asked about (`59bfcb3`, `d7cfde5`).

## Status

Accepted, `abbcab7` (2026-09-08).

## Related

- [AGENT_CHAIN.md - TONY](../AGENT_CHAIN.md#tony---classify)
