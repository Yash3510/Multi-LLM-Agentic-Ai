---
title: Licences and the licence gate
type: architecture
status: active
owner: R4
updated: 2026-10-17
covers:
  - tools/licence_gate.py
  - tools/import_scan.py
  - tools/sbom.py
  - tools/licence-review.toml
tags: [4ce, architecture, licences]
---

# Licences and the licence gate

4CE owns its code and ships nothing it can't legally ship. Every build generates an SBOM and fails on any dependency the policy doesn't allow. `just licences` runs all three steps, and `just check` includes it.

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
   - **Approvals by ADR.** A review-required licence passes only for a package an ADR approved: `[[approved]]` in `tools/licence-review.toml` names the package, its exact licence and the ADR ([ADR-0037](../adr/0037-licence-approvals-for-the-backend-stack.md) approves psycopg, psycopg-binary, certifi and cffi). A changed licence lapses the approval.
   - **4CE's own packages** (`fource-*`) are skipped, and commercially licensed libraries pass here; the import scan limits where they are used.
3. **Import scan.** [`tools/import_scan.py`](../../tools/import_scan.py) parses every import in `core/`, `apps/` and `packs/`, finds the package that provides it, and fails if that package is copyleft without a commercial licence. A commercial library may be imported only where its adapter lives; PyMuPDF has no adapter yet, so it may be imported nowhere. An import that no installed package provides also fails.

4. **Third-party bundle.** `tools/licence_gate.py --bundle` checks that every bundled service ships its licence, notices, exact version and source; see [bundled services](services.md#the-third-party-bundle).

**Scope today:** the Python environment, including development tools, and the bundled services. The npm side arrives with `apps/web`.

## Measured

On 2026-10-12, at commit `99ccbf9`, on Linux: `just licences` checked 30 components and scanned 6 files with no problems. On Windows (CI) the environment also holds `colorama`, whose metadata only says "BSD License"; its LICENSE.txt was read and recorded as BSD-3-Clause. Without `licence-review.toml`, exactly the packages it lists fail.

## Decisions

[ADR-0015](../adr/0015-licence-allowlist-and-sbom-gate.md) (the gate) and [ADR-0023](../adr/0023-third-party-services.md) (third-party services); [ADR-0036](../adr/0036-mpl-build-tools-and-licence-mapping.md) is proposed.
