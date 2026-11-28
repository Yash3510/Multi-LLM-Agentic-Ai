---
title: Licences and the licence gate
type: architecture
status: active
owner: R4
updated: 2026-11-22
covers:
  - tools/licence_gate.py
  - tools/import_scan.py
  - tools/sbom.py
  - tools/licence-review.toml
tags: [4ce, architecture, licences]
---

# Licences and the licence gate

4CE owns its code and ships nothing it can't legally ship. Every build generates an SBOM and fails on any dependency the policy doesn't allow. `just licences` runs all four steps, and `just check` includes it.

## The policy

Master plan Appendix A. Changing it is R4's decision, recorded in an ADR; it is never changed to get a build green.

| Class | Licences | Rule |
| --- | --- | --- |
| Allowed anywhere | MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0, ISC, PostgreSQL, PSF-2.0, Zlib, HPND, Unicode, OFL-1.1 (fonts), CC0-1.0, CC-BY-4.0 (data, with attribution) | Use freely, through our interfaces |
| Allowed as an unmodified separate service | AGPL-3.0, including Redis's AGPL option | Never imported into 4CE code and never modified. Licence, notices and source ship with every image and update. |
| Allowed as a library only under a commercial licence | AGPL or GPL libraries whose owner sells one | Signed before the first install outside the team. Today: PyMuPDF (Artifex). |
| Review required | MPL-2.0, LGPL-2.1/3.0, EPL-2.0; vendor redistributable runtimes | Only unmodified, as a separate process or dynamic link, and only after an ADR |
| Denied | SSPL, RSAL, BSL, Commons Clause, Elastic License; AGPL or GPL code imported without a commercial licence; non-commercial licences | Never shipped |

## How the gate works

1. **SBOM.** [`tools/sbom.py`](../../tools/sbom.py) writes the CycloneDX SBOM of the synced Python environment to `build/sbom/python.cdx.json`, using `cyclonedx-bom` 7.5.0 through `uvx`. The SBOM is generated, never committed.
2. **Licence gate.** [`tools/licence_gate.py`](../../tools/licence_gate.py) reads the SBOM and fails on any component whose licence isn't allowed anywhere:
   - **Expressions are strict.** Every licence in an `AND` or `OR` expression must be allowed. Electing one option of an `OR` is proposed in [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) and waits on R4.
   - **Unclear metadata is read by a person.** Some packages only say "BSD License". Someone reads the package's LICENSE file and records the licence in [`tools/licence-review.toml`](../../tools/licence-review.toml), pinned to that version, so an update is read again.
   - **Approvals by ADR.** A review-required licence passes only for a package an ADR approved: `[[approved]]` in `tools/licence-review.toml` names the package, its exact licence and the ADR ([ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md) approves psycopg, psycopg-binary, certifi, cffi and, for the CA list it bundles, botocore). A changed licence lapses the approval.
   - **4CE's own packages** (`fource-*`) are skipped, and commercially licensed libraries pass here; the import scan limits where they are used.
3. **Import scan.** [`tools/import_scan.py`](../../tools/import_scan.py) parses every import in `core/`, `apps/` and `packs/`, finds the package that provides it, and fails if that package is copyleft without a commercial licence. A commercial library may be imported only where its adapter lives; PyMuPDF has no adapter yet, so it may be imported nowhere. An import that no installed package provides also fails.

4. **Third-party bundle.** `tools/licence_gate.py --bundle` checks that every bundled service ships its licence, notices, exact version and source; see [bundled services](services.md#the-third-party-bundle).

**Scope today:** the Python environment, including development tools, and the bundled services. `apps/web` is on `4ce-core`, but its npm packages aren't checked yet: reading the npm SBOM waits on ADR-0036 ([frontend](frontend.md)).

## Measured

On 2026-10-12, at commit `99ccbf9`, on Linux: `just licences` checked 30 components and scanned 6 files with no problems. On Windows (CI) the environment also holds `colorama`, whose metadata only says "BSD License"; its LICENSE.txt was read and recorded as BSD-3-Clause. Without `licence-review.toml`, exactly the packages it lists fail.

On 2026-10-17, with `apps/server` and its dependencies installed on Linux, `just licences` checked 52 components and scanned 27 files with no problems. `uvloop` (pulled in by `uvicorn[standard]` on Linux and macOS) says only "Apache Software License" and "MIT License" as classifiers; its two LICENSE files were read and it is recorded as `MIT OR Apache-2.0`, both options allowed anywhere.

Later on 2026-10-17, with `httpx` added for the API tests, `just licences` checked 62 components and scanned 47 files with no problems. `httpx` names BSD-3-Clause in its metadata and again the classifier "BSD License", which the gate cannot match; its LICENSE.md was read and recorded as BSD-3-Clause. `certifi` (the certificate bundle `httpx` loads, approved by ADR-0037 as MPL-2.0) names MPL-2.0 twice in its metadata, once as an SPDX id and once as a classifier text the gate cannot match, and an approval needs a single value; its LICENSE file (the MPL 2.0 notice) was read and recorded as MPL-2.0, so the approval holds.

**Sign-in and ledger dependencies.** `pyjwt[crypto]` (the token library of [identity](identity.md#tokens)) pulls in `cryptography`; the extra is kept because pyright's strict mode needs it. `cryptography` 50.0.2 declares `Apache-2.0 OR BSD-3-Clause` in its installed metadata (`License-Expression`; its `dist-info/licenses` folder holds LICENSE, LICENSE.APACHE and LICENSE.BSD). Both options are allowed anywhere, so the strict gate passes it with no entry in `licence-review.toml`. `fource-ledger` depends on `cryptography` directly, for Ed25519 checkpoints ([ledger](ledger.md)); same version and licence, no new component.

On 2026-10-25, at commit `88c1cfa`, on Linux, with the ledger added, `just licences` checked 63 components and scanned 67 files with no problems, and checked the 5 bundled services.

**Queue and live-state dependencies.** `redis` 8.1.0 (redis-py, the client of the bundled Redis) declares `License-Expression: MIT` and has no runtime dependencies on Python 3.12; it is imported only in `core/live`. `fource-jobs` now depends on `psycopg` directly (for LISTEN), approved by [ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md). fakeredis was not added (BSD-3-Clause, but it would bring sortedcontainers, whose metadata says only "Apache 2.0"; [ADR-0026](../adr/0026-redis-for-live-state.md)).

On 2026-10-31, at commit `aab1c6c`, on Linux, with the queue and the live store added, `just licences` checked 66 components and scanned 93 files with no problems, and checked the 5 bundled services.

**Storage dependencies.** `fource-storage` ([file storage](storage.md)) depends on boto3 and urllib3 directly. Installed with them, at the locked versions:

| Package | Version | Licence | Role |
| --- | --- | --- | --- |
| boto3, botocore, s3transfer | 1.44.5, 1.44.5, 0.19.3 | Apache-2.0 | The S3 client, imported only in `core/storage` |
| jmespath, six, urllib3 | 1.1.0, 1.17.0, 2.8.0 | MIT | botocore's runtime dependencies |
| python-dateutil | 2.9.0.post0 | Apache-2.0 and BSD-3-Clause | botocore's runtime dependency |
| types-boto3-lite, types-boto3-s3, botocore-stubs, types-s3transfer | 1.44.3, 1.44.0, 1.43.126, 0.19.3 | MIT | Type stubs, development only |

- **Three packages go through [`tools/licence-review.toml`](../../tools/licence-review.toml)**: s3transfer and python-dateutil, read from their licence files on 2026-11-17, and botocore, read on 2026-11-21 (below, with its approval). s3transfer says "Apache License 2.0" with a classifier the gate can't match (its LICENSE.txt is the Apache 2.0 text); python-dateutil says only "Dual License" (its LICENSE puts contributions since 2017-12-01 under Apache-2.0 and all the code under BSD-3-Clause), recorded as `Apache-2.0 AND BSD-3-Clause`.
- **botocore's CA bundle.** botocore's code is Apache-2.0, but its NOTICE puts the Mozilla CA root certificates it ships, `botocore/cacert.pem`, under MPL-2.0: the same file certifi carries. The project lead approved it on certifi's terms on 2026-11-21 ([ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md) point 2): used unmodified, and never read, because botocore uses certifi's copy whenever certifi is installed, as it is in 4CE. `tools/licence-review.toml` records botocore as `Apache-2.0 AND MPL-2.0`, and an `[[approved]]` entry names ADR-0037 for exactly that expression.

On 2026-11-21, at commit `b4f3487`, on Linux, with file storage added, `just licences` checked 78 components and scanned 114 files with no problems, and checked the 5 bundled services ([log](../log/2026/11/2026-11-21-wp-f-08-file-storage.md#how-it-was-verified)).

## Decisions

[ADR-0015](../adr/0015-licence-allowlist-and-sbom-gate.md) (the gate), [ADR-0023](../adr/0023-third-party-services.md) (third-party services), [ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md) (the approvals) and [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) (MPL-2.0 build tools and the licence mapping); all four are proposed.
