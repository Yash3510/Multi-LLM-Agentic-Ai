---
title: MinIO patch source
type: research
status: unverified
owner: R4
updated: 2026-10-12
tags: [4ce, research, deploy, licences]
---

# MinIO patch source

Input for ADR-0025 (MinIO as the object store, and its patch source), which the master plan wants decided before the first pilot.

## Question

MinIO's community edition no longer ships images or patches. Where do 4CE's object-store builds and security fixes come from?

## What was checked, 2026-10-12

Verified with the commands shown:

| Fact | How |
| --- | --- |
| `minio/minio` on GitHub is archived; last push 2026-04-24; last release `RELEASE.2025-10-15T17-29-55Z` (commit `9e49d5e7`) | `gh api repos/minio/minio`, `gh api repos/minio/minio/releases/latest` |
| The `minio/minio` Docker Hub repository no longer exists | `https://hub.docker.com/v2/repositories/minio/minio/` returns 404 |
| `quay.io/minio/minio` refuses anonymous access | the Quay API returns 401 |
| `pgsty/silo` (formerly `pgsty/minio`) is active: AGPL-3.0, not archived, last push 2026-10-08, releases 2026-06-18, 2026-08-04, 2026-08-06, 2026-09-03, 2026-09-16 | `gh api repos/pgsty/silo`, `gh api repos/pgsty/silo/releases` |
| Its images are on Docker Hub as `pgsty/silo` (latest `RELEASE.2026-09-16T00-00-00Z`, plus distroless variants); the old `pgsty/minio` tags stop at 2026-08-04 | Docker Hub tags API |
| The fork's own commits come mostly from one maintainer (Vonng); the other top contributors are upstream MinIO history | `gh api repos/pgsty/silo/contributors` |
| SeaweedFS and RustFS are Apache-2.0; Garage is AGPL-3.0; all three pushed in October 2026; RustFS's latest release is 1.0.1 | `gh api repos/<repo>` |

Unverified, from the projects' own pages and press: that the 2025-10-15 release fixed CVE-2025-62506; that the fork backports later CVE fixes and keeps `MINIO_*` settings, metrics and on-disk format compatible; that its releases ship checksums, SBOMs and signed provenance. Sources: [Silo on GitHub](https://github.com/pgsty/silo), [Silo's site](https://silo.pgsty.com/), [the maintainer's announcement](https://blog.vonng.com/en/db/minio-resurrect/), [pgsty/minio on Docker Hub](https://hub.docker.com/r/pgsty/minio), [Linuxiac on the fork](https://linuxiac.com/open-source-community-launches-minio-fork/), [StableBuild on the removed images](https://www.stablebuild.com/blog/minio-images-disappeared-from-docker-hub).

## Options

| Option | Licence | Patches | Change for 4CE | Risks |
| --- | --- | --- | --- | --- |
| **Build the last release from source** (what development uses today) | AGPL-3.0 | None after 2025-10-15 | None | Known vulnerabilities accumulate; not fit for a pilot |
| **PGSTY Silo** | AGPL-3.0 | Roughly monthly releases with backported fixes (claimed) | An image swap; MinIO compatibility claimed | One maintainer; no foundation; claims need checking against its changelog |
| **Commercial MinIO (AIStor)** | Commercial | Vendor | A licence and an image swap | Cost; terms must cover redistribution in an appliance |
| **Replace it behind the S3 interface:** SeaweedFS or RustFS (Apache-2.0), Garage (AGPL-3.0) | as listed | Active upstreams | A different service behind `core/storage`; operations and docs change | Behaviour differences; a permissive option also removes an AGPL service from the bundle |

## What it changes

- **Development now:** `deploy/config/minio/minio.dockerfile` builds `RELEASE.2025-10-15T17-29-55Z` unmodified from its tag and checks the commit; the third-party bundle records it.
- **Before the first pilot (ADR-0025):** pick a patch source. The smallest change is PGSTY Silo, after its changelog and signatures are checked. If removing an AGPL service matters to buyers, test SeaweedFS behind the S3 interface first.
