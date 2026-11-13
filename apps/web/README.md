# apps/web

The 4CE user interface: a SvelteKit app built as a static single-page app. `4ce-server` serves the
build and returns `200.html` for every path that is not `/api` or `/ws`. There is no Node process
at run time and no server-side rendering ([ADR-0035](../../docs/adr/0035-frontend-foundations.md) §2).

The design values and rules live in [design-system.md](../../docs/architecture/design-system.md).

## Commands

Node 24 and npm. Run from this folder, or use the matching `just` recipe from the repo root.

| Command               | What it does                                                              |
| --------------------- | ------------------------------------------------------------------------- |
| `npm ci`              | Install exactly what `package-lock.json` pins                             |
| `npm run dev`         | Live-reloading dev server                                                 |
| `npm run build`       | Static build into `build/` (with `.br` and `.gz` copies)                  |
| `npm run preview`     | Serve the production build                                                |
| `npm run check`       | Types (svelte-check)                                                      |
| `npm run lint`        | ESLint and Prettier                                                       |
| `npm run format`      | Rewrite files in Prettier style                                           |
| `npm run lint:design` | Design lint: palette classes, arbitrary values, stray hex, blur and glass |
| `npm test`            | Unit and component tests (Vitest, jsdom), plus the repo tools' tests      |
| `npm run e2e`         | Playwright against the production build on port 4310                      |
| `npm run icons`       | Generate the icon components                                              |
| `npm run i18n`        | Compile the messages with Paraglide                                       |

`dev`, `build`, `check` and `test` run `icons` and `i18n` first, because both outputs are
generated and never committed. Playwright needs its browser once: `npx playwright install chromium`.

## Where things live

| Path                         | Contents                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------- |
| `src/routes/`                | Pages only: load data, compose components                                       |
| `src/routes/ui/sections/`    | The `/ui` design reference: one `NN-name.svelte` per section, in file order     |
| `src/lib/ui/`                | The design system: tokens, base components, theme, motion, formatting           |
| `src/lib/ui/tokens/`         | The only files allowed to hold raw colour values                                |
| `src/lib/ui/icons/generated` | Icon components from `tools/icons` (generated, not committed)                   |
| `src/lib/components/<area>/` | Feature components                                                              |
| `src/lib/i18n/messages/`     | UI strings per locale (`en.json`, `hi.json`); missing keys fall back to English |
| `src/lib/i18n/generated/`    | Paraglide output (generated, not committed)                                     |
| `src/app.html`               | Page shell, with the script that sets theme and motion before first paint       |
| `e2e/`                       | Playwright tests (desktop 1440×900, tablet 820×1180)                            |
| `project.inlang/`            | Paraglide settings; only `settings.json` is committed                           |

## Settings kept in the browser

All under `localStorage`, read with a guard because storage can be blocked:

| Key           | Values                              |
| ------------- | ----------------------------------- |
| `4ce.theme`   | `system`, `light`, `dark`           |
| `4ce.motion`  | `system`, `reduce`                  |
| `4ce.density` | `comfortable`, `default`, `compact` |
| `4ce.locale`  | `en`, `hi`                          |

The locale is read and written by a Paraglide custom strategy in `src/lib/i18n/locale.ts`, because
Paraglide's own localStorage strategy uses an unguarded key of its own. Call `setLocale` from the
generated runtime; never write the key directly.
