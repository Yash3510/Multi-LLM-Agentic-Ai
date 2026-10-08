---
title: MPL-2.0 build and test tools, and the licence mapping
type: adr
status: planned
owner: R4
updated: 2026-10-08
covers:
  - apps/web/package.json
  - tools/licence_gate.py
tags: [4ce, adr, licences]
number: 36
decision_status: proposed
superseded_by: null
---

# ADR-0036: MPL-2.0 build and test tools, and the licence mapping

## Context

The licence gate (master plan §2.5) fails on any licence that Appendix A doesn't list. Appendix A puts MPL-2.0 under "review required: only unmodified, as a separate process or dynamic link, and only after an ADR".

Resolving the frontend toolchain chosen in [ADR-0035](0035-frontend-foundations.md) on 2026-10-08 gave 550 packages. Their licences:

| Licence                                                                                             | Packages |
| --------------------------------------------------------------------------------------------------- | -------- |
| MIT                                                                                                 | 358      |
| ISC                                                                                                 | 78       |
| Apache-2.0                                                                                          | 35       |
| MPL-2.0                                                                                             | 26       |
| Apache-2.0 WITH LLVM-exception                                                                      | 13       |
| BlueOak-1.0.0                                                                                       | 13       |
| BSD-2-Clause                                                                                        | 11       |
| BSD-3-Clause                                                                                        | 4        |
| Each of: OFL-1.1, 0BSD, MIT OR CC0-1.0                                                              | 2        |
| Each of: Python-2.0, MPL-2.0 OR Apache-2.0, CC-BY-3.0, CC0-1.0, MIT AND CC-BY-3.0, no licence field | 1        |

The MPL-2.0 packages can't be avoided:

- **lightningcss** (12 platform binaries) is a direct dependency of Vite 8 and of Tailwind CSS 4.
- **axe-core**, through @axe-core/playwright, is the standard accessibility checker for browser tests.

None of them ends up in the static build that ships.

Several other licences are permissive but not named in Appendix A. Without a decision, the gate fails on the first commit of `apps/web`.

Changing the licence policy is a human decision (AGENTS.md §3), so this record proposes and R4 decides.

## Decision (proposed)

1. **MPL-2.0 is allowed for build-time and test-time tools that are used unmodified and never shipped.** Today that means:
   - lightningcss and its platform binaries
   - axe-core
   - @axe-core/playwright

   The gate tells shipped dependencies apart from build and test dependencies. Shipped means the production dependency closure plus a scan of the built bundle. The SBOM lists the build and test tools with their scope. An MPL-2.0 package that reaches the shipped bundle still fails the gate.

2. **These permissive licences are added to "allowed anywhere":**
   - BlueOak-1.0.0
   - 0BSD
   - Python-2.0 (the PSF licence Appendix A already allows, under its SPDX name)
   - Apache-2.0 WITH LLVM-exception
   - CC-BY-3.0 and MIT AND CC-BY-3.0 (licence data inside SPDX tooling), with attribution in the notices
3. **OR expressions.** For a package offered under several licences, 4CE elects one that Appendix A allows and records the choice in the SBOM and the notices. DOMPurify is under MPL-2.0 OR Apache-2.0, and 4CE elects Apache-2.0.
4. **Missing licence fields.** When a package's registry entry has no licence field, a person reads its LICENSE file and records the result in a reviewed mapping file next to the gate. Today:
   - svelte-toolbelt 0.10.6 is MIT
   - @inlang/plugin-message-format 4.4.5 is MIT

## Alternatives considered

- **Avoid MPL-2.0 entirely.** That means no Vite 8 and no Tailwind 4, and no axe. That gives up the plan's chosen stack (§6.3) and automated accessibility checks.
- **A general "dev dependencies don't count" rule.** Too broad: it would let any licence into tooling without review. Naming each one keeps review honest.

## Consequences

- Appendix A gains the entries above (R4's change).
- `tools/licence_gate.py` gains the shipped-versus-tooling split, OR elections and the reviewed mapping file.
- New MPL-2.0 tools still need their own review. This record names today's packages only.

## Status

Proposed on 2026-10-08. Needs R4's acceptance before `apps/web` is added, since the gate fails without it.

## Evidence

- **Licence fields:** read from the npm registry for each package.
- **LICENSE files:** read for DOMPurify, svelte-toolbelt and the Paraglide plugin.
- **The 550-package tree:** resolved with `npm install --package-lock-only --ignore-scripts` for the ADR-0035 set.
- **Caveat:** this is a policy classification, not legal advice.
