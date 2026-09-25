---
title: 4CE documentation
type: index
status: active
updated: 2026-09-25
tags:
  - 4ce
---

# 4CE documentation

Everything written about 4CE, in one place. Pages describe the committed
code; where a page records a measurement, it names the commit it was measured
at.

---

## Start here

| If you want to... | Read |
|---|---|
| Run it on Windows or Linux | [HOW_TO_RUN.md](HOW_TO_RUN.md) |
| Run it on a Mac, from nothing | [SETUP_MACOS.md](SETUP_MACOS.md) |
| Present it | [DEMO_SCRIPT.md](DEMO_SCRIPT.md) |
| Understand how it is built | [ARCHITECTURE.md](ARCHITECTURE.md), then [AGENT_CHAIN.md](AGENT_CHAIN.md) |
| Check a claim it makes | [TESTING.md](TESTING.md), and the verification table in the [project README](../../README.md#verification-status) |
| Know why it is built this way | [decisions/](#decisions) |
| See how it got here | [history/](history/README.md) and [CHANGELOG.md](CHANGELOG.md) |

---

## Documents in this folder

| Document | Type | Status | What it covers |
|---|---|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | architecture | active | Components, one request end to end, storage, trust boundaries |
| [AGENT_CHAIN.md](AGENT_CHAIN.md) | agent | active | TONY, the router, the image reading pass, the deterministic steps, FRIDAY, JARVIS, ULTRON, the replan, the sign-off, release |
| [TESTING.md](TESTING.md) | testing | active | The tool suite, preflight, the retrieval and vision evals, hand-verified results, known limits |
| [HOW_TO_RUN.md](HOW_TO_RUN.md) | deployment | active | Setup from source, models at 8192, preflight, egress rules, adding a model, reading images, recovering retrieval |
| [SETUP_MACOS.md](SETUP_MACOS.md) | deployment | active | A clean first run on macOS |
| [DEMO_SCRIPT.md](DEMO_SCRIPT.md) | workflow | active | Nine prompts with measured timings, and the questions to pre-empt |
| [SOP_THRESHOLD_PLAN.md](SOP_THRESHOLD_PLAN.md) | design | implemented | The rule-pack engine's design, with where the implementation now differs |
| [deep-research.md](deep-research.md) | research | historical | Source-reading study of the platform, written before the build |
| [CHANGELOG.md](CHANGELOG.md) | changelog | active | Notable changes by date |

### Decisions

| ADR | Decision |
|---|---|
| [0001](decisions/0001-agent-chain-as-a-runtime-plugin.md) | Build the agent chain as a runtime plugin |
| [0002](decisions/0002-fail-closed-human-approval.md) | Human approval fails closed |
| [0003](decisions/0003-verify-on-a-different-model.md) | Verify on a different model |
| [0004](decisions/0004-deterministic-tools-for-arithmetic.md) | Arithmetic and checks run in code, not in a model |
| [0005](decisions/0005-load-models-at-8192-context.md) | Load the models at 8192 context |
| [0006](decisions/0006-route-by-a-model-registry.md) | Route by a model registry |
| [0007](decisions/0007-observe-egress-rather-than-assert-it.md) | Observe egress rather than assert it |
| [0008](decisions/0008-answer-conversation-directly.md) | Answer conversation directly |

### History

The [development timeline](history/README.md) groups every commit into
seventeen milestones, from the [foundation](history/2026-09-08-foundation.md)
to [reading images into fields](history/2026-09-25-reading-images-into-fields.md).

---

## Elsewhere in the repository

| Document | What it covers |
|---|---|
| [README.md](../../README.md) | The project overview, and the verification status table |
| [4ce/README.md](../README.md) | The orchestrator's valve reference and design notes |
| [SECURITY.md](../../SECURITY.md) | The threat model: what "sovereign" covers and what it does not |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | What is 4CE's code and what is the platform's, and why plugin ids are `ace_*` |
| [docs/SECURITY.md](../../docs/SECURITY.md) | The upstream platform's own vulnerability-reporting policy |

---

## Conventions

- **Frontmatter.** Every page here starts with `title`, `type`, `status`,
  `updated` and `tags`, which Obsidian reads as properties.
- **Status.** One of `active`, `implemented`, `experimental`, `planned`,
  `deprecated`, `historical` or `unverified`. Nothing planned is described as
  built, and nothing untested as verified.
- **Tags.** A small set: `4ce`, `architecture`, `agent`, `model`, `security`,
  `testing`, `deployment`, `research`, `decision`, `git-history`.
- **Links.** Relative markdown links, not `[[wikilinks]]`, so they resolve both
  on GitHub and in the Obsidian vault at the repository root.
- **One home per subject.** Other pages link to it rather than repeat it: the
  valve reference is in `4ce/README.md`, the threat model is in `SECURITY.md`,
  and the verification table is in the project README.
- **Keeping it current.** When code changes, update the page whose subject
  changed and add the commit to the [timeline](history/README.md#maintaining-this-page).
  The timeline records the last commit it has processed.
