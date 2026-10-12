---
title: "Third-party services"
type: adr
status: implemented
owner: R4
updated: 2026-10-12
covers: []
tags: [4ce, adr, licences, deploy]
number: 23
decision_status: proposed
superseded_by: null
---

# ADR-0023: Third-party services: unmodified, separate, with their source

## Context

The stack uses MinIO, Redis 8, Grafana and (as an add-on) Firecrawl, all under AGPL-3.0, alongside PostgreSQL and Prometheus. The master plan's position (§2.7) is that AGPL obligations reach code linked with or derived from the licensed work, not a separate program that talks to it over the network, provided the licence, notices and source of what is shipped go with it. That position is a policy, not legal advice; the legal review below confirms or corrects it.

## Decision

1. **AGPL services run unmodified, as separate services,** reached only over the network through 4CE's own interfaces. A needed change goes upstream, or the component is replaced behind its adapter.
2. **No AGPL code is imported into 4CE.** The import scan enforces it.
3. **`deploy/third-party/<service>/`** holds each service's `LICENSE` and `NOTICE` from upstream at the exact commit, `VERSION` (the image in use) and `SOURCE` (tag, commit and archive). It ships with every image and update; the bundle check enforces it.
4. **Images are pinned by digest**, or built from a recorded upstream commit.
5. **A legal review** happens before the first commercial sale and is recorded in this ADR's successor; a one-page note for buyers' legal teams is ready before the first government deal.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Avoid every AGPL service | Gives up the stack the plan chose; permissive replacements stay possible behind the adapters |
| Bundle without notices and source | Breaks the licence the moment an appliance leaves the team |

## Consequences

- Grafana's image reports a build commit that is not in its public repository; `deploy/third-party/grafana/SOURCE` records it, and the legal review must settle what source 4CE points to.
- MinIO publishes source only now; its patch source is ADR-0025's decision (see [MinIO patch source](../research/minio-patch-source.md)).
- A permissive replacement for an AGPL service would remove it from the buyer's legal note.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made; the legal review is still to come. To be accepted by R4.
