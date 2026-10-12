---
title: Frontend foundations
type: adr
status: planned
owner: R3
updated: 2026-10-08
covers:
  - apps/web/
tags: [4ce, adr, frontend]
number: 35
decision_status: proposed
superseded_by: null
---

# ADR-0035: Frontend foundations

## Context

The master plan (v3.8) chooses SvelteKit, Tailwind CSS and an owned component library for the UI (§6.3), puts it in `apps/web` (§6.4), and requires a clean room: nothing from the upstream project, including its CSS, strings, icons and configuration (§2.4). It leaves several choices open: how the UI is served, which icon set and font, accessibility, theming, languages, devices and testing. Some of its choices also disagree with later decisions (icons) or with each other (role names: four in §1, seven in §2.6, six in WP-PS-02).

Today's chat UI is the earlier fork. The 4CE team wrote about 30 of its components (about 6,300 lines in 26 files by one author, plus the Sovereignty page). Everything around them is upstream and has to be built new. An audit of our own components (2026-10-08) found:

- about 40 animation durations and 13 easing curves across 15 files
- seven focus styles, none reaching 3:1 contrast
- meta text in a grey that measures 2.78:1 on white
- four ways to show a verdict
- a grey scale that arrived with the fork import

None of that can carry over as it is.

This record settles the frontend's foundations before any code is written. The design values themselves live in [the design system page](../architecture/design-system.md).

## Decision

### 1. Stack and versions

Pinned exactly in `apps/web/package.json`, with the committed `package-lock.json` (§6.5). The versions and licences come from the npm registry on 2026-10-08 (see Evidence).

| Concern                          | Package                                                                            | Version               | Licence                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------- | --------------------- | -------------------------------------------------------------------- |
| Framework                        | svelte                                                                             | 5.57.x                | MIT                                                                  |
| App framework                    | @sveltejs/kit                                                                      | 2.70.3                | MIT                                                                  |
| Static output                    | @sveltejs/adapter-static                                                           | 3.0.10                | MIT                                                                  |
| Bundler                          | vite, @sveltejs/vite-plugin-svelte                                                 | 8.3.3, 7.3.1          | MIT                                                                  |
| Types                            | typescript                                                                         | 5.9.3                 | Apache-2.0                                                           |
| CSS                              | tailwindcss, @tailwindcss/vite                                                     | 4.3.3                 | MIT                                                                  |
| Behaviour primitives (headless)  | bits-ui (+ peer @internationalized/date)                                           | 2.19.5 (3.12.x)       | MIT (Apache-2.0)                                                     |
| Icons source                     | @phosphor-icons/core (dev only; components generated)                              | 2.1.1                 | MIT                                                                  |
| Markdown                         | marked                                                                             | 18.1.0                | MIT                                                                  |
| HTML sanitiser                   | dompurify, under its Apache-2.0 option                                             | 3.4.16                | MPL-2.0 OR Apache-2.0                                                |
| Translations                     | @inlang/paraglide-js (+ @inlang/plugin-message-format vendored)                    | 2.26.0 (4.4.5)        | MIT                                                                  |
| API types and client             | openapi-typescript, openapi-fetch                                                  | 7.13.0, 0.17.0        | MIT                                                                  |
| Fake API until the backend lands | msw                                                                                | 3.0.2                 | MIT                                                                  |
| Unit and component tests         | vitest, @testing-library/svelte                                                    | 5.0.3, 5.4.2          | MIT                                                                  |
| Browser tests                    | @playwright/test (browsers pre-staged for offline CI)                              | 1.64.0                | Apache-2.0                                                           |
| Accessibility checks             | @axe-core/playwright                                                               | 4.13.0                | MPL-2.0, see [ADR-0036](0036-mpl-build-tools-and-licence-mapping.md) |
| Format, lint, types              | prettier (+ prettier-plugin-svelte), eslint (+ eslint-plugin-svelte), svelte-check | 3.9.9, 10.12.0, 4.7.6 | MIT                                                                  |
| Licence check and SBOM           | license-checker-rseidelsohn, @cyclonedx/cyclonedx-npm                              | 5.0.1, 6.0.1          | BSD-3-Clause, Apache-2.0                                             |
| Fonts                            | @fontsource-variable/inter, @fontsource-variable/noto-sans-devanagari              | 5.3.0                 | OFL-1.1                                                              |
| Mono font                        | IBM Plex Mono, self-hosted                                                         | —                     | OFL-1.1, unverified: confirm in the licence gate                     |

- **SvelteKit 2.70, not 3.0.** SvelteKit 3.0 was released on 2026-10-01. Its TypeScript 6 peer conflicts with openapi-typescript, which supports TypeScript 5 only (npm ERESOLVE, reproduced). The 2.70 set above resolves cleanly, with no overrides and no duplicate packages. We revisit SvelteKit 3 at M1.
- **Node 24 LTS** for the frontend toolchain. vitest 5 and msw 3 need at least 22.12, and the licence checker needs 24.
- **The licence checker.** license-checker (last released 2019) is replaced by its maintained fork, plus the CycloneDX generator for the npm SBOM (§2.5).

### 2. How the UI is served

- **A static single-page build.** adapter-static writes a fallback page (`200.html`) and precompressed files.
- **`4ce-server` serves it.** Every path that isn't `/api` or `/ws` returns the fallback page.
- **One origin.** The session cookie is HttpOnly and SameSite=Strict, with a CSRF header on writes (§7.3).
- **No Node process at run time and no server-side rendering.** This keeps the nine processes of §6.2.
- **Needs R1's agreement,** because `apps/server` gains the static mount and the fallback route.

### 3. Live updates

- **One WebSocket** carries a run's events, each with the run id and a sequence number.
- **Reconnecting resumes the run.** On connect or reconnect, the client loads the run's state from the run store and replays events after the last sequence it saw.
- **The stage rail is a pure function of run state,** so a reload, a dropped connection or a second tab shows the same rail.

### 4. API contract and fake data

- **Generated types.** TypeScript types are generated from the server's OpenAPI document at build time and never committed (§6.4).
- **Fake API in the meantime.** Until an endpoint exists, MSW serves fixtures typed against the same contract. That lets the frontend move ahead of the backend.
- **Synthetic data only.** Fixtures use the synthetic demo data from the packs. Customer data never appears in them.

### 5. Roles and labels

- **Six roles, in this order:** Planner, Reader, Analyst, Author, Challenger, Sign-off. Router is internal and not shown. TONY, FRIDAY, JARVIS and ULTRON are not used anywhere.
- **Labels come from the active pack's vocabulary.** That includes subject names ("Asset", "Application"), the gate's role name ("Inspection Head") and the parameters.
- **`apps/web` contains no sector words.** The neutrality check covers it (WP-F-04).

### 6. Devices

- **Desktop (1024 px and wider):** first class.
- **Tablet (768–1023 px):** supported for review, sign-off and capturing evidence.
- **Phones:** later.
- **Touch targets:** at least 24 × 24 px everywhere (WCAG 2.5.8), and 44 px for a tablet's primary actions.

### 7. Languages

- **English ships at the pitch, built Hindi-ready.**
  - Every string goes through Paraglide.
  - Pack labels come per locale.
  - Each message sets its own `lang`.
  - Layouts are screenshot-tested in Hindi.
- **The Paraglide plugin is vendored.** Its default setup downloads the plugin from a CDN during the build, which an offline appliance can't do.
- **The typed release word is always `approve`,** in every language. The panel explains it in the active language. Typing is guarded against input-method composition.

### 8. Theme

- **System, light and dark from day one.**
- **A theme is a token swap** on `<html data-theme>`, with `color-scheme` set. Components never write `dark:` classes.

### 9. Accessibility

WCAG 2.2 AA, and in particular:

- **Focus:** one focus outline on every control (2 px, offset 2 px) at 3:1 or better.
- **Keyboard:** every hover behaviour has a keyboard equivalent, and tooltips are focusable popovers, not `title` attributes.
- **Sign-off:** fully operable by keyboard and by screen reader.
- **CI:** axe runs in CI, plus a test that measures every text colour on every surface.

### 10. The design system

- **Owned tokens in three tiers:** primitives, semantic roles and component aliases. They live in `apps/web/src/lib/ui/tokens`, with Tailwind's default palette switched off.
- **The values and rules are in [design-system.md](../architecture/design-system.md).** It sets the bar above today's UI:
  - **Colour:** one neutral family; text tiers that all pass 4.5:1; violet reserved for live agent work and focus; one hue per verdict (ok, caution, stop).
  - **Type and shape:** eight type steps, six radii, and four opaque elevation levels.
  - **Motion:** named durations and easings, written motion rules, and one reduced-motion switch.
  - **Components:** a full state matrix for every component, one number-format module, three densities, a command palette, an owned data table, and print styles for records.
- **The upstream grey scale is not reused.**

### 11. No glass

- **Opaque surfaces only:** no frosted or translucent panels, `backdrop-filter`, blur, sheen, gloss, inner highlights or refraction.
- **Depth** comes from surface steps, hairlines and soft shadows.
- **A design lint enforces it.**

### 12. Icons

- **Everyday icons are Phosphor** (MIT): the regular weight on its 256 grid, and bold at 16 px and below.
- **4CE's own concepts get an owned signature set,** drawn on the same grid and taking their construction from the logo (true 30° hexagons) without ever containing the logo:
  - the verdicts PASS, REVIEW, FAIL and NO DATA
  - rule, observation, pack, skill, ledger, evidence pack, sign-off, Challenger
  - "could not check"
- **Roles use Phosphor glyphs:** Planner `path`, Reader `scan`, Analyst `list-magnifying-glass`, Author `pen-nib`.
- **One generator builds everything.** `tools/icons`, run as `just icons`, writes `apps/web/src/lib/ui/icons`. That output is generated and not committed; the signature sources are committed. The generator rejects filters, gradients, masks, transforms and any opacity other than the single 0.2 duotone layer.
- **Icons move only on a live state change,** play once, and show their final frame under reduced motion.
- **The hexagon verdict badges are previewed in the real app before adoption.** Phosphor's circle icons are the fallback.

### 13. Quality gates

- **A design lint** rejects raw palette classes, arbitrary values, hex colours outside the token files, `backdrop-filter`, and scaling above 1.
- **An owned `/ui` route** renders every component in every state.
- **Playwright snapshots** cover that route and the pitch-demo screens in light, dark, reduced motion, Hindi and print.
- **The pitch demo script is a browser test.**

### 14. Clean room

- **Nothing comes from upstream:** no CSS, colour scale, strings, icon names, configuration (including its SvelteKit config), modal or tooltip.
- **Our own components are rebuilt on the new tokens from their behaviour, not copied.** That covers the stage rail, node glyph, approval panel, receipt, audit sheet, file card, revision card, logo motion, run error card and Sovereignty page, following the porting rule in §3.

## Alternatives considered

| Option                                   | Why not                                                                                                     |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| SvelteKit 3.0 now                        | One week old, and its TypeScript 6 peer conflicts with the API type generator. Revisit at M1.               |
| Server-side rendering (adapter-node)     | Adds a Node process that §6.2 doesn't have; an appliance UI needs no SEO.                                   |
| Lucide (the plan's default)              | Allowed, but the app already uses Phosphor, which also has the weights and duotone the signature set needs. |
| Iconly Pro                               | Its terms forbid redistribution and modification without written permission; an appliance redistributes.    |
| A fully owned icon set                   | The most work, and a hand-drawn set was rejected before. Owned glyphs are limited to 4CE's own concepts.    |
| svelte-i18n                              | Untyped keys, and no release since 2024.                                                                    |
| A styled kit (shadcn-svelte and similar) | Brings someone else's look. bits-ui gives behaviour and accessibility only.                                 |
| Frosted glass                            | Rejected by the user; it also renders differently on appliance GPUs and on paper.                           |
| Box-shadow focus rings                   | Clipped by `overflow: hidden` and lost in Windows forced-colours mode.                                      |

## Consequences

- **Master plan corrections** (human-owned, for R1). These are proposed, not made:
  - §6.3: icons become Phosphor plus the owned set; fonts become Inter, Noto Sans and IBM Plex Mono; the licence checker becomes the maintained fork plus CycloneDX.
  - Role names: unify §1, §2.6 and WP-PS-02 on the six roles.
  - Appendix A: per [ADR-0036](0036-mpl-build-tools-and-licence-mapping.md).
- **New work packages** for the screens the plan lacks. They come from the screen inventory (frontend step 2).
- **`apps/server`** needs a static mount and a fallback route (R1).
- **Each component costs more at first** (all states, tests and snapshots). We accept that, because it is what makes the UI consistent.
- **The marketing website (a separate repository)** still uses frosted glass, Google-hosted fonts and the old agent names. That is a follow-up there, not part of this decision.

## Status

Proposed on 2026-10-08 by the frontend owner. To be accepted by:

- the frontend owner, for all of it: accepted on 2026-10-08
- R1, for §2 (serving) and §5 (role names): pending
- R4, for [ADR-0036](0036-mpl-build-tools-and-licence-mapping.md): pending

Frontend work proceeds against this record. The parts R1 decides only take effect when the frontend connects to the real server.

## Evidence

- **Versions and licences:** `curl -s https://registry.npmjs.org/<package>/latest` and the full registry documents for publish dates (2026-10-08).
- **Licence files:** read from the package files.
- **Dependency trees:** resolved with `npm install --package-lock-only --ignore-scripts`, so no package code ran.
- **Design audit:** our own components in the fork at commit `92b062a`, read only.
- **Icon geometry:** measured from `npm pack @phosphor-icons/core@2.1.1`.
- **Unverified:** run-time behaviour of the chosen set; openapi-typescript on TypeScript 6; the IBM Plex Mono licence check.
