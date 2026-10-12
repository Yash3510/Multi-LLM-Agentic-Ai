# Every command the team runs. Recipes stay one-line calls to uv so they behave the
# same on Windows, macOS and Linux; anything with logic lives in tools/.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# List the recipes
default:
    @just --list

# Install Python through uv and sync every package
setup:
    uv python install
    uv sync --all-packages

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

# Every CI check, locally, exactly as CI runs it
check: lint repo-check test
