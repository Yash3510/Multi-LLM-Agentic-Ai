# Sovereign AI Documentation

## SIH 2026 — Problem Statement 26117

### Documentation Set

1. [Master Architecture](docs/architecture/00_MASTER_ARCHITECTURE.md)
2. [Phase 1 — Foundation](docs/phases/01_PHASE_1_FOUNDATION.md)
3. [Phase 2 — Stark Multi-Agent Runtime](docs/phases/02_PHASE_2_STARK_AGENTS.md)
4. [Phase 3 — Industrial Document AI & RAG](docs/phases/03_PHASE_3_INDUSTRIAL_AI.md)
5. [Phase 4 — Tools, Sandbox & Deliverables](docs/phases/04_PHASE_4_TOOLS_SANDBOX.md)
6. [Phase 5 — Verification & Human-in-the-Loop](docs/phases/05_PHASE_5_VERIFICATION.md)
7. [Phase 6 — Sovereign Security](docs/phases/06_PHASE_6_SOVEREIGN_SECURITY.md)
8. [Phase 7 — Polish & SIH Demo](docs/phases/07_PHASE_7_POLISH_DEMO.md)

Demo and security runbooks: [Demo guide](docs/guides/DEMO.md) and [Sovereign security](docs/guides/SECURITY.md).

Verification reports are grouped under [`docs/verification`](docs/verification/).

Setup and run instructions: [RUNNING.md](RUNNING.md).

## Recommended Build Order

```text
Phase 1
  ↓
Phase 2
  ↓
Phase 3
  ↓
Phase 4
  ↓
Phase 5
  ↓
Phase 6
  ↓
Phase 7
```

Each phase assumes the previous phase is implemented and tested. Do not rewrite completed phases unless a genuine architectural defect requires it.

## Relationship to `4CE`

This is the original architecture spec and a standalone, tested-end-to-end reference implementation (`sovereign_ai/`). The current implementation effort forks Open WebUI (see [`../4CE`](../4CE/README.md)) and ports the agent loop, sandbox, and citation-discipline guard in as plugins — see [`4CE/deep-research.md` §15](../4CE/deep-research.md#15-mapping-our-existing-sovereign_ai-work-onto-this-fork) for the mapping. **This repo is kept as the fallback demo** and should not be deleted or rewritten. See also the [top-level project README](../README.md).
