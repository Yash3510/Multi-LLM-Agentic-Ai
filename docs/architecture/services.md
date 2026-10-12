---
title: Bundled services
type: architecture
status: active
owner: R4
updated: 2026-10-12
covers:
  - deploy/compose/
  - deploy/config/
  - deploy/third-party/
tags: [4ce, architecture, deploy]
---

# Bundled services

The services 4CE talks to over the network. Each runs unmodified as its own container; 4CE's code never imports them (see [licences](licences.md)).

| Service | Version | Licence | Used for |
| --- | --- | --- | --- |
| PostgreSQL | 18.6 | PostgreSQL | State, cases, the ledger, the job queue, full-text search, row-level security |
| Redis | 8.10.2 | AGPL-3.0 (of its three options) | Live events, short caches, locks, rate limits. Jobs and run state stay in PostgreSQL, so a Redis restart loses no work. |
| MinIO | `RELEASE.2025-10-15T17-29-55Z`, built from source | AGPL-3.0 | Originals, page renders, deliverables, pack bundles |
| Prometheus | 3.15.0 | Apache-2.0 | Operations metrics |
| Grafana | 13.2.3 (OSS) | AGPL-3.0 | Operations dashboards for admins, later reached through the 4CE login |

## Running them

```
just dev     # build MinIO the first time, start everything, wait until healthy
just down    # stop everything; the data volumes are kept
```

Both read `.env` (copy [`.env.example`](../../.env.example) and replace every `change-me`); the stack refuses to start without its passwords. `just dev` publishes each service on `127.0.0.1` only: PostgreSQL 5432, Redis 6379, MinIO 9000 (console 9001), Prometheus 9090, Grafana 3000.

## How they are set up

- **[`deploy/compose/core.yml`](../../deploy/compose/core.yml)** is the stack itself. Every service sits on an internal network with no route out, runs with a read-only root file system, drops every Linux capability (adding back only what an entrypoint needs to hand its data folder to an unprivileged user), cannot gain privileges, and has a health check. Pulled images are pinned by digest.
- **[`deploy/compose/dev.yml`](../../deploy/compose/dev.yml)** publishes the ports for development. Publishing needs a second, non-internal network, which also gives the services a route out, so it never ships in an appliance.
- **Nothing phones home.** Grafana's usage reporting, update and plugin checks, news feed, Gravatar, external snapshots and plugin preinstalls are off; MinIO's update check and call-home are off.
- **Configuration** lives in `deploy/config/<service>/`: Prometheus's scrape list, Grafana's provisioned Prometheus data source, and the MinIO build.

## MinIO

MinIO's community edition is archived and publishes source only, so [`minio.dockerfile`](../../deploy/config/minio/minio.dockerfile) builds the last release from its upstream tag, unmodified, and fails if the tag no longer points at the recorded commit. That release gets no security patches: it is for development. The patch source for pilots is ADR-0025's decision; the options are compared in [MinIO patch source](../research/minio-patch-source.md).

## The third-party bundle

`deploy/third-party/<service>/` holds each service's `LICENSE` and `NOTICE` (from upstream, at the exact commit), `VERSION` (the image in use, then the upstream version) and `SOURCE` (the upstream tag, commit and source archive). `just licences` fails when an image has no complete folder, when `VERSION` doesn't name the image in use, when a pulled image isn't pinned by digest, or when a folder belongs to no service.

## Measured

On 2026-10-12, on the Debian laptop (Docker 26.1.5): `docker compose config` accepts the merged files with `.env.example`, and refuses to start without the passwords. The start-up result is recorded in the [work log](../log/README.md).
