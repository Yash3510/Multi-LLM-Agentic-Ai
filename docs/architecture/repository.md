---
title: Repository layout and working rules
type: architecture
status: active
owner: R1
updated: 2026-10-12
covers:
  - justfile
  - pyproject.toml
  - tools/repo_check.py
  - .editorconfig
  - .gitattributes
  - .gitignore
tags: [4ce, architecture, repository]
---

# Repository layout and working rules

One repository holds all of 4CE: code, packs, tests, docs and deployment. **Every file has exactly one obvious home.** If a file's home isn't obvious, the structure is wrong, not the file: raise it in review and fix the structure, with an ADR if the layout changes.

[`tools/repo_check.py`](../../tools/repo_check.py) enforces the checkable rules on this page (`just repo-check`).

## Layout

Folders marked _planned_ don't exist yet; they arrive with their work packages.

| Path | Holds | State |
| --- | --- | --- |
| `.github/` | `CODEOWNERS`, `pull_request_template.md`, `ISSUE_TEMPLATE/`, `dependabot.yml`, `workflows/` | partly built |
| `.obsidian/` | shared vault settings only: `app.json`, `core-plugins.json`, `templates.json` | built |
| `apps/server/` | the FastAPI app: thin wiring, no business logic | _planned_ |
| `apps/web/` | the SvelteKit UI and Pack Studio | _planned_ |
| `core/<package>/` | sector-neutral Python packages, all uv workspace members | `common` built |
| `packs/sector/<pack-id>/`, `packs/cross/<pack-id>/` | one industry or one department each | _planned_ |
| `skills/<skill-name>/` | 4CE's built-in skills | _planned_ |
| `tests/` | tests that cross package boundaries: `integration/`, `e2e/`, `security/` | _planned_ |
| `evals/` | the eval harness; golden data lives in each pack | _planned_ |
| `deploy/` | `compose/`, `config/<service>/`, `installer/`, `systemd/`, `third-party/<component>/` | _planned_ |
| `docs/` | the knowledge base and Obsidian vault ([documentation rules](documentation.md)) | built |
| `tools/` | repository scripts, each run through a `just` command | built |

**The root holds only** the folders above plus `.editorconfig`, `.env.example`, `.gitattributes`, `.gitignore`, `.pre-commit-config.yaml`, `.python-version`, `justfile`, `pyproject.toml`, `uv.lock`, `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md` and `SECURITY.md`. Anything else at the root fails the repo check.

### Core packages

Every `core/*` package (and `apps/server`) has the same shape:

```
core/rules/
├── pyproject.toml          name = "fource-rules"; its dependencies are declared here only
├── README.md               purpose, public API, owner, links to its ADRs
├── src/fource/rules/
│   ├── __init__.py         the public API, listed in __all__
│   ├── py.typed            marks the package as typed
│   ├── engine.py           one clear responsibility per module
│   └── _internal/          private helpers, never imported from another package
└── tests/
    ├── test_engine.py      one test file per module, same name
    └── fixtures/           small test data only
```

- **One namespace.** All Python lives under `fource` (`from fource.rules import evaluate`), because a Python name can't start with a digit.
- **Public API only.** Another package imports only what a package exports in its `__init__.py`.
- **Every package has a README and tests.** The repo check fails a package missing either.

### Boundaries

- `core/*` packages depend only on `common` and on other packages' public APIs.
- `core/*` never imports from `packs/*`; packs are loaded at run time.
- `packs/*` hold mostly data; any pack code depends only on the published Pack SDK.
- `apps/*` wire everything together and hold no business logic.
- `tools/` may import anything, and nothing imports `tools/`.

import-linter enforces these as contracts in `pyproject.toml` (`just imports`). Today: `common` imports no other 4CE package, and each package's modules are imported only through its `__init__.py`. `just new-package` adds that public-API contract for every new package. The apps-above-core contract arrives with `apps/server`, and the packs rule with the Pack SDK.

## Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Folders | kebab-case (Python package folders inside `src/` are snake_case) | `finance-expenses/`, `third-party/` |
| Python modules | snake_case | `fource/rules/engine.py` |
| Python classes, functions | PascalCase, snake_case | `RulePack`, `evaluate_band()` |
| Svelte components | PascalCase | `SignOffPanel.svelte` |
| TypeScript modules | camelCase | `trustView.ts` |
| Pack ids and pack file names | kebab-case | `industrial-energy`, `sop-mec-014.json` |
| Ids inside packs | snake_case, namespaced by pack | `industrial-energy/seal_leak` |
| ADRs | `NNNN-kebab-title.md` | `0018-sector-neutral-core.md` |
| Tests | `test_<module>.py`; end-to-end tests by scenario | `test_two_pack.py` |
| Environment variables | `FOURCE_` prefix, upper snake case | `FOURCE_DATABASE_URL` |
| Branches | `<type>/<work-package-or-topic>` | `wp/RL-01-rule-engine-core` |

Other files are lower case. Upper-case names are limited to `README.md`, `CHANGELOG.md`, `AGENTS.md` and the third-party `LICENSE`, `NOTICE`, `VERSION` and `SOURCE` files, plus the root files above and the names GitHub requires in `.github/`.

**Banned in any file or folder name:** version or status words (`v2`, `final`, `new`, `old`, `backup`, `copy`, `temp`, `test2`), spaces, and dates. Dates are allowed only where the docs rules require them: `docs/log/`, `docs/history/` and `docs/assurance/`. Git keeps the history; file names don't.

## Where does it go?

| You're adding… | It goes in… |
| --- | --- |
| An API endpoint | `apps/server/src/fource/server/routes/<area>.py`, with the logic in the `core/` package that owns it |
| Business logic | The `core/` package that owns it. If no package owns it, write an ADR before writing code. |
| Anything specific to one industry or department | A pack under `packs/`, never `core/` |
| A UI page | `apps/web/src/routes/` |
| A reusable UI element | `apps/web/src/lib/ui/` |
| A feature component | `apps/web/src/lib/components/<area>/` |
| A rule, calculator, document kind, workflow or template | The matching folder of the pack it belongs to |
| A test of one package | That package's `tests/` |
| A test across packages | `tests/integration/`, `tests/e2e/` or `tests/security/` |
| Golden documents and answer keys | The pack's `evals/`, stored through Git LFS |
| A script the team runs | `tools/`, plus a `just` command that runs it |
| Configuration for a bundled service | `deploy/config/<service>/` |
| A decision | `docs/adr/` |
| A secret | Nowhere in the repo: a git-ignored `.env` locally, the installer's secret store on appliances |

## Never in the repo

- Secrets, keys, certificates and `.env` files. Only `.env.example` is committed.
- Model weights, and customer data of any kind, even anonymised.
- Build outputs (`node_modules/`, `.venv/`, `.svelte-kit/`, `build/`, `dist/`, `__pycache__/`) and generated artefacts (SBOMs, notices bundles, API clients, coverage reports).
- Logs, caches, local databases and uploaded files.
- Obsidian per-person files: `.obsidian/workspace*.json`, caches, plugin state.
- Tool-specific agent instruction or configuration files. [`AGENTS.md`](../../AGENTS.md) files are the only agent instructions committed.
- Binaries over 1 MB outside Git LFS, Jupyter notebooks, commented-out code, and `TODO`s without an issue number.
- Personal scratch files. Exclude these in your own `.git/info/exclude`, not in the shared `.gitignore`.

## Working rules

### Branches

- **`main` is always releasable** and protected: no direct or force pushes, linear history, required checks, signed commits only.
- **All work happens on short-lived branches off `main`:** `wp/<WP-id>-<short-title>`, `fix/<topic>`, `docs/<topic>`, `chore/<topic>`, `pack/<pack-id>-<topic>`.
- **`release/<x.y>` branches** exist only to patch a version installed at a customer; fixes land on `main` first.

### Commits

- **Commit after every finished step:** a failing test, the code that passes it, a refactor, a docs page, an ADR, the log entry, a review fix. Each is its own commit, under about 100 changed lines, and leaves the tree working.
- **Conventional Commits, scoped to the package or pack:** `feat(rules): add authority rule type`. The message says why, not just what.
- **Every commit counts on its author's profile:** a verified email on your own GitHub account, signed commits, and a `Co-authored-by:` trailer only for a teammate who genuinely paired.
- **Never padding:** no empty or whitespace-only commits, no change split artificially, no bots, nothing that breaks the build. The repo check rejects empty, whitespace-only and non-conventional commits (`uv run python tools/repo_check.py --commits <range>`).

### Pull requests

- **One work package or one fix per PR,** under about 400 changed lines plus tests. The title is a Conventional Commit.
- **To merge:** every check green, every touched folder's code owner approved, all conversations resolved. Trust-critical code (`core/policy`, `core/ledger`, `core/signoff`, `core/sandbox`, pack signing) needs two approvals.
- **Rebase and merge only, never squash,** so every commit lands on `main` with its author intact.
- **Push as you go:** push after every finished step and before stopping; open a draft PR after the first push.

### Checks

`just check` runs every check locally, exactly as CI does.

| Check | Tool | State |
| --- | --- | --- |
| Python formatting and lint | ruff | built |
| Python types | pyright (strict for `core/`) | built |
| Repo hygiene | [`tools/repo_check.py`](../../tools/repo_check.py) | built |
| Sector neutrality | [`tools/neutrality_check.py`](../../tools/neutrality_check.py) | built |
| Tests | pytest | built |
| Frontend formatting, lint and types | prettier, eslint, svelte-check | _planned_ with `apps/web` |
| Package boundaries | import-linter (`just imports`) | built |
| Licences, imports and SBOM | [`tools/licence_gate.py`](../../tools/licence_gate.py), [`tools/import_scan.py`](../../tools/import_scan.py) ([licences](licences.md)) | built |
| Third-party bundle | `tools/licence_gate.py` | _planned_ with the Compose stack |
| Secrets | gitleaks | _planned_ |
| Docs | [`tools/docs_check.py`](../../tools/docs_check.py) | built |

### Commands

| Command | Does |
| --- | --- |
| `just setup` | Install Python through uv and sync every package |
| `just test` | Unit tests |
| `just lint` | Formatting, lint and types |
| `just repo-check` | The repo check |
| `just imports` | The package-boundary contracts |
| `just neutrality` | The neutrality check |
| `just licences` | The SBOM, licence gate and import scan |
| `just docs` | The docs check; add `--base origin/main` for the PR rules |
| `just new-package <name>` | Scaffold `core/<name>/` from the package template and install it |
| `just new-doc <type> <name>` | Create a docs page or work-log entry from its template (`just new-doc log <branch-name>`) |
| `just check` | Every check, as CI runs it |

### Dependencies: uv for everything Python

uv installs Python, creates environments, adds packages, locks and runs. pip is never used, and nothing in the repo tells anyone to run it.

| Task | Command |
| --- | --- |
| Install the right Python version | `uv python install` (reads `.python-version`) |
| Set up or refresh everything | `uv sync --all-packages` (`just setup` does this) |
| Add a dependency to a package | `uv add --package fource-rules pint` |
| Add a development-only tool | `uv add --dev pytest` |
| Update one dependency | `uv lock --upgrade-package pint` |
| Run anything in the project environment | `uv run pytest` |
| Install in CI and in images | `uv sync --frozen` |

- `pyproject.toml` declares dependencies and the one `uv.lock` pins them. No `requirements.txt`, `setup.py`, `Pipfile` or `poetry.lock`.
- A new dependency is named in its PR with its licence.
- The frontend uses npm with its committed `package-lock.json`.

### Line endings, editors and large files

- `.gitattributes` forces LF line endings and routes PDF, PNG, JPG, XLSX, DOCX and PPTX files through Git LFS.
- `.editorconfig` sets 4-space indents for Python and 2 for everything else, a final newline, and trimmed trailing whitespace.
- Anything over 1 MB that isn't in LFS fails the repo check.
