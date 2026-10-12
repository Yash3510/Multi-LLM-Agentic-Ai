---
title: State
type: state
status: active
owner: R1
updated: 2026-10-12
tags: [4ce, state]
---

# State

Where 4CE stands right now. Updated at the weekly planning and at every milestone.

## What works

Phase 0's foundations, on `4ce-core`, the trunk of [Yash3510/Multi-LLM-Agentic-Ai](https://github.com/Yash3510/Multi-LLM-Agentic-Ai) (the latest work is not yet pushed). Evidence: on 2026-10-12, a fresh clone ran `just setup` and `just check` with exit 0 on Linux, as recorded in [the work log](log/2026/10/2026-10-12-4ce-core.md).

- **The repository and its checks:** the [layout and working rules](architecture/repository.md), enforced by the repo check, the neutrality check, the import contracts, the [docs check](architecture/documentation.md#the-docs-check), the [licence gate, import scan and bundle check](architecture/licences.md), gitleaks and the commit-message hook. CI runs `just check` on Linux, Windows and macOS (not yet run on GitHub).
- **[`core/common`](../core/common/README.md):** typed settings.
- **[`core/packs`](../core/packs/README.md):** the draft Pack and Rule Pack JSON Schemas.
- **The [bundled services](architecture/services.md):** PostgreSQL, Redis, MinIO, Prometheus and Grafana start healthy with `just dev`.
- **The knowledge base:** this index, the templates, the shared Obsidian settings and seven proposed ADRs.

## In progress

Nothing on a branch. The rest of Phase 0 waits on the open questions below.

## Open questions

- **ADR-0035 and ADR-0036** (frontend foundations; MPL-2.0 build tools) wait on R1 and R4. `apps/web`, the design tokens and the npm side of the licence gate wait on them.
- **The proposed ADRs** 0009, 0015, 0018, 0023, 0029, 0031 and 0032 need their owners' acceptance.
- **ADR-0025:** MinIO's patch source; options in [MinIO patch source](research/minio-patch-source.md).
- **CODEOWNERS:** which GitHub handle holds each of R1 to R4.
- **Legal review:** Grafana's image reports a build commit that isn't in its public repository.

## Next up

1. Decide the open questions above, make `4ce-core` the default branch on GitHub, and push.
2. Run CI on GitHub; fix anything Windows or macOS shows.
3. Reach M0: `apps/server` with a login (WP-F-06, WP-ID-01), and `apps/web` once ADR-0035 is accepted.
