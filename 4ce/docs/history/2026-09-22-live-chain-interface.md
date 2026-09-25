---
title: The live chain interface
type: git-history
status: historical
date: 2026-09-22
commits: [8256bb6, 4214451, d119bbb, 0044412, 76e4ed2, a011443, 8841962, 40b8e2c, dacda0d, dcfdac3, c6aae4a, 2a0250c, bc2d1a1, e670f03, d3218e5, b717f74, 9dcce39, 132f50b, 252c301, 33dac53, eba3068, 8157ad4]
authors: [Pranay Harish Munj]
tags:
  - 4ce
  - git-history
---

# The live chain interface

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `8256bb6` | 2026-09-22 | Pranay Harish Munj | Show the agent chain as it works: orb, stage rail, live status, sign-off panel |
| `4214451` | 2026-09-23 | Pranay Harish Munj | Overview: show each run as a tree that runs straight down |
| `d119bbb` | 2026-09-23 | Pranay Harish Munj | Open with the 4CE intro, and animate the mark while the chain works |
| `0044412` | 2026-09-23 | Pranay Harish Munj | Polish: the rail ends on a dot, and corners nest |
| `76e4ed2` | 2026-09-23 | Pranay Harish Munj | Land the sign-in intro on the sidebar button in a narrow window |
| `a011443` | 2026-09-23 | Pranay Harish Munj | Polish the chat area: corners, motion and small details |
| `252c301` | 2026-09-23 | Pranay Harish Munj | Preview the Word report before downloading it |
| `132f50b` | 2026-09-23 | Pranay Harish Munj | Welcome on the empty chat: the mark, what to ask, suggestion cards |
| `8841962` | 2026-09-23 | Pranay Harish Munj | Sharper answer formatting: tables, headings, lists, code, quotes |
| `40b8e2c` | 2026-09-23 | Pranay Harish Munj | Refresh the backend's copy of the 4CE stylesheet |
| `dacda0d` | 2026-09-23 | Pranay Harish Munj | Bring the report preview up like motion graphics |
| `dcfdac3` | 2026-09-23 | Pranay Harish Munj | Plain logo, no motion in the Overview, one corner scale for the chat |
| `c6aae4a` | 2026-09-23 | Pranay Harish Munj | Task lines for suggestions; a report preview you can read |
| `2a0250c` | 2026-09-23 | Pranay Harish Munj | Rail nodes as rings, a light that hands over, one job per line |
| `bc2d1a1` | 2026-09-23 | Pranay Harish Munj | Slow, text-sized light on the working name and status line |
| `e670f03` | 2026-09-23 | Pranay Harish Munj | A calmer, clearer sign-in page |
| `d3218e5` | 2026-09-23 | Pranay Harish Munj | Sign-in: keep typed and autofilled text readable in dark mode |
| `b717f74` | 2026-09-23 | Pranay Harish Munj | A stopped run says what went wrong and how to fix it |
| `9dcce39` | 2026-09-23 | Pranay Harish Munj | Restore the original suggestions |
| `33dac53` | 2026-09-24 | Pranay Harish Munj | Trust view in answers, the route as you type, both switchable |
| `eba3068` | 2026-09-24 | Pranay Harish Munj | Leave cut-off check lines out of every list of checks |
| `8157ad4` | 2026-09-24 | Pranay Harish Munj | Mark each chat in the sidebar by how its run ended |

## Summary

The chain became visible as it runs. A stage rail, a live status line and an
animated mark follow each agent. A tree overview shows every run, a card
explains failures, and the sidebar marks each chat by how its run ended.

## Why it changed

Every step already emitted a status event, but the interface showed them as
plain lines. These commits make the chain's actual execution readable at a
glance.

## Files changed

Frontend only, apart from `8157ad4`:

- `src/lib/components/chat/Messages/ResponseMessage/` (`StageRail.svelte`, `NodeGlyph.svelte`, `StatusHistory/LiveStatusLine.svelte`, `RunErrorCard.svelte`)
- `src/lib/components/chat/Overview/` (`summary.js`, `Flow.svelte`, `Node.svelte`, `AgentNode.svelte`, `View.svelte`)
- `src/lib/components/common/ThinkingOrb.svelte`, `LogoMotion.svelte`, `logoMotion.js`; `static/static/4ce-intro.js`
- `src/lib/components/chat/Messages/trustView.js`, `chat/MessageInput/RoutePreview.svelte`, `common/InterfaceSettings.svelte`
- `src/routes/auth/+page.svelte`, `src/lib/components/auth/AuthField.svelte`
- `backend/open_webui/utils/fource.py`, `models/chats.py`, `routers/chats.py` (`8157ad4`)

## Technical changes

- **Stage rail** (`8256bb6`, `2a0250c`, `bc2d1a1`, `0044412`). A node for each
  of TONY, FRIDAY, JARVIS, ULTRON and the human gate, timed by the server. A
  replan is drawn as an arc back to FRIDAY. One light hands over from stage to
  stage, and the status line says only what is happening.
- **Overview tree** (`4214451`). Each agent pass stacks down its own column,
  "try 2" after a failed check, with an amber "sent back" wire.
- **Intro and mark motion** (`d119bbb`, `76e4ed2`, `dcfdac3`). A one-time intro
  after sign-in that assembles the mark and lands it on the sidebar logo. The
  mark animates beside a running answer and stays still under reduced motion.
- **Failure card** (`b717f74`). The cause in plain words, the agent it stopped
  at, numbered fix steps, a copyable command, and Try again.
- **Trust view and route preview** (`33dac53`). Answer sentences are
  underlined by what they rest on. Under the message box, a line shows where
  a request will go before it is sent. Both can be switched off under
  Settings → Interface → 4CE.
- **Sidebar outcome marks** (`8157ad4`). Released, withheld, stopped, or
  finished without sign-off. Read on the server and cached in the chat's meta.
- **Word report preview** (`252c301`, `dacda0d`, `c6aae4a`). The first page of
  the real `.docx`, drawn in the browser.
- **Visual polish** (`a011443`, `8841962`, `40b8e2c`, `132f50b`, `9dcce39`,
  `e670f03`, `d3218e5`, `eba3068`). Corner radii, motion, answer typography at
  4.5:1 contrast or better, the empty-chat welcome, the sign-in page, and
  hiding cut-off check lines. The suggestion list was redesigned twice and
  returned to its original form (`9dcce39`).

## Impact

This milestone changed the interface only. The orchestrator's behaviour was
unchanged, apart from the status details it emits.

## Related documentation

- [ARCHITECTURE.md - frontend additions](../ARCHITECTURE.md#frontend-additions---srclibcomponents)
- [Timeline](README.md)
