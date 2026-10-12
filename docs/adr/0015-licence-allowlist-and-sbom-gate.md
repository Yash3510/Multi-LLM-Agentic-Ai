---
title: "Licence allowlist and SBOM gate"
type: adr
status: implemented
owner: R4
updated: 2026-10-12
covers: []
tags: [4ce, adr, licences]
number: 15
decision_status: proposed
superseded_by: null
---

# ADR-0015: Licence allowlist and SBOM gate

## Context

4CE ships an appliance to customers, including government buyers who ask for an SBOM. A copyleft library imported by accident would put 4CE's own code under that licence. Master plan §2.5 and Appendix A set the policy; this record decides how it is enforced.

## Decision

1. **Every build generates a CycloneDX SBOM** and fails on any dependency whose licence the policy doesn't allow anywhere. The policy is Appendix A and lives in [the licences page](../architecture/licences.md); changing it is R4's decision.
2. **The gate is strict.** Every licence in an expression must be allowed; a package whose metadata doesn't name its licence is read by a person and recorded, for that exact version, in `tools/licence-review.toml`.
3. **An import scan** fails if 4CE code imports a copyleft library without a commercial licence, and limits a commercially licensed library (PyMuPDF) to the module that adapts it.
4. **A bundle check** fails unless every bundled service ships its licence, notices, exact version and source.
5. All of it runs in `just licences`, inside `just check`, locally and in CI.

## Alternatives considered

| Option | Why not |
| --- | --- |
| A review at release time only | Too late: by then the dependency is built in |
| A general "development dependencies don't count" rule | Lets any licence into tooling without review; ADR-0036 proposes naming each exception instead |
| license-checker for Python and npm | Two tools and two formats; the SBOM is generated anyway, so the gate reads it |

## Consequences

- A new dependency with an unclear licence stops the build until someone reads its licence.
- Electing one option of an `OR` licence, and MPL-2.0 build tools, wait on [ADR-0036](0036-mpl-build-tools-and-licence-mapping.md).
- The npm side is added with `apps/web`.

## Status

Proposed on 2026-10-12. Records a decision master plan v3.8 already made. To be accepted by R4.
