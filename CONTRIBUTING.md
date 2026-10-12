# Contributing

The short version of how we work. The full rules, and the reasons for them, are in [docs/architecture/repository.md](docs/architecture/repository.md) and [docs/architecture/documentation.md](docs/architecture/documentation.md).

## Every working session

1. Start from the latest `4ce-core`.
2. Work from an issue, on a branch named `wp/<WP-id>-<short-title>` (or `fix/`, `docs/`, `chore/`, `pack/`). Never on `4ce-core`.
3. Read [docs/state.md](docs/state.md) and the docs pages for the area you will touch.

## Making a change

- **Put each file where the layout says.** Industry words go in a pack, never in `core/` or `apps/`; the neutrality check enforces it.
- **Tests first for logic:** branches, parsers, transforms, money, auth, security.
- **Commit after every finished step:** a failing test, the code that passes it, a refactor, a docs page, the log entry. Each commit is small, working and a Conventional Commit: `feat(rules): add authority rule type`. The message says why.
- **Python means uv:** `uv add --package fource-rules pint`, `uv run pytest`. Never pip.
- **Name every new dependency and its licence** in the PR. The licence gate fails anything the policy doesn't allow.
- **Document it in the same PR:** one work-log entry (`just new-doc log <branch-name>`), every page whose `covers` you touched, and an ADR for any decision.
- **Run `just check`** before you ask for review. It runs exactly what CI runs.

## Pull requests

- **One work package or one fix per PR,** under about 400 changed lines plus tests. Push after every finished step and open a draft PR after the first push.
- **To merge:** every check green, the code owner of every touched folder approved, all conversations resolved. Trust-critical code (`core/policy`, `core/ledger`, `core/signoff`, `core/sandbox`, pack signing) needs two approvals.
- **Rebase and merge, never squash,** so every commit lands with its author.

## Coding agents

Anyone may use a coding agent. It works under the same rules as a person, plus [AGENTS.md](AGENTS.md):

- **One instruction file.** `AGENTS.md` is the only agent instruction file in the repository. If your tool wants another file name, create a one-line local pointer to `AGENTS.md` and exclude it in your own `.git/info/exclude`. The repo check fails a committed tool-specific file.
- **Least privilege.** An agent gets a developer's normal repository access and nothing more: no production or customer environments, no cloud credentials, no signing keys. It connects only to local or R4-approved services.
- **Human-only actions.** Agents never merge, approve, push to `4ce-core`, force-push, sign anything, or change CI, branch protection, CODEOWNERS, the licence policy, the risk tiers or `AGENTS.md`.
- **You are the author.** The person who opens the PR is accountable for every line. Commits, PRs, comments and docs carry no tool attribution.
