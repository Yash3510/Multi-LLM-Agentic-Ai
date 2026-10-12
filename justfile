# Every command the team runs. Recipes stay one-line calls to uv so they behave the
# same on Windows, macOS and Linux; anything with logic lives in tools/.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# List the recipes
default:
    @just --list

# Install Python through uv, sync every package and install the git hooks
setup:
    uv python install
    uv sync --all-packages --locked
    uv tool install pre-commit
    pre-commit install --install-hooks --allow-missing-config

# Unit and integration tests
test:
    uv run pytest

# Formatting, lint and types
lint:
    uv run ruff format --check .
    uv run ruff check .
    uv run pyright

# Layout, naming, package and dependency-file rules (§6.4, §6.5)
repo-check:
    uv run python tools/repo_check.py

# No sector vocabulary in core/ or apps/ (§9)
neutrality:
    uv run python tools/neutrality_check.py

# Frontmatter, links, orphans, names, state and history of docs/ (§6.6)
docs *args:
    uv run python tools/docs_check.py {{args}}

# Scaffold a core package from the template
new-package name:
    uv run python tools/scaffold.py package {{name}}
    uv sync --all-packages

# Create a docs page or work-log entry from its template
new-doc type name:
    uv run python tools/scaffold.py doc {{type}} {{name}}

# Package boundaries: only public APIs cross packages (§6.4)
imports:
    uv run lint-imports

# SBOM, licence gate and import scan (§2.5); the SBOM lands in build/sbom/
licences:
    uv run python tools/sbom.py
    uv run python tools/licence_gate.py build/sbom/python.cdx.json
    uv run python tools/import_scan.py build/sbom/python.cdx.json
    uv run python tools/licence_gate.py --bundle

# Start the bundled services on localhost and wait until they are healthy (needs .env)
dev:
    docker compose --env-file .env -f deploy/compose/core.yml -f deploy/compose/dev.yml up --detach --build --wait

# Stop the bundled services; their data volumes are kept
down:
    docker compose --env-file .env -f deploy/compose/core.yml -f deploy/compose/dev.yml down

# No secrets anywhere in the branch's history (gitleaks)
secrets:
    pre-commit run gitleaks-history --hook-stage manual --all-files

# Every CI check, locally, exactly as CI runs it
check: lint imports repo-check neutrality docs licences secrets test
