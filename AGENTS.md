# AGENTS.md

Rules for every coding agent working in this repository, whatever the tool.
They apply on top of everything a human contributor follows.
If a rule here conflicts with your task, stop and ask a human.

## 1. Before you start
- Start from the latest `4ce-core`: run `just sync`.
- Read this file, `docs/state.md`, and the docs pages for the area you will
  touch (`docs/README.md` lists them).
- Work only from a work-package or bug issue. Restate its goal and acceptance
  tests before writing code. If either is unclear, ask.
- Create a branch named `wp/<WP-id>-<short-title>` (or `fix/`, `docs/`,
  `chore/`, `pack/`). Never work on `4ce-core`.
- Run `git status`. If there are changes you didn't make, leave them alone.

## 2. Stay in scope
- Touch only the files and folders the work package names. Put each new file
  where `docs/architecture/repository.md` says it belongs.
- No drive-by refactors, renames or reformatting. Open an issue for anything
  else you notice.
- Industry-specific content goes in `packs/`, never in `core/` or `apps/`.

## 3. Never do these: they are for humans
- Merge or approve a PR, push to `4ce-core`, force-push, or rewrite published
  history.
- Change CI workflows, branch protection, CODEOWNERS, the licence policy, the
  risk-tier defaults, or this file.
- Sign anything: packs, releases, installers, ledger checkpoints.
- Delete data, drop tables, wipe volumes, `git reset --hard`, `rm -rf`, or
  anything else irreversible, unless the human asked for that exact action in
  this task.

## 4. Secrets and data
- Never read, print, copy or commit secrets, keys, tokens or `.env` files.
  Use placeholders in `.env.example`.
- Customer data never enters your context: not in prompts, files, fixtures or
  logs. Use the synthetic data in `packs/*/demo/`.
- Never send repository content to a service that isn't local or approved.

## 5. Dependencies and code origin
- Python: `uv add`, `uv sync`, `uv run`. Never `pip`. Frontend: `npm install`,
  `npm ci`.
- Check a new dependency's licence against the licence policy before adding
  it, and name it with its licence in the PR.
- Never import an AGPL, GPL, SSPL, RSAL or BSL library. PyMuPDF is the one
  commercially licensed exception.
- Never copy code from other projects, including the archived fork. Write it
  from the specs.

## 6. Never weaken a check
Don't skip or delete tests, mark them expected-to-fail, lower thresholds, add
ignore comments (`noqa`, `type: ignore`, `eslint-disable`), loosen a policy,
or edit golden eval data to match your output. If a check looks wrong, say so
and let a human decide, and record their decision in the log entry.

## 7. Architecture rules
- Import only a package's public API (its `__init__.py`).
- Where a written rule exists, decide in code (rule engine, calculators),
  never by model judgement.
- Check policy before accessing data. Never filter afterwards.
- Every new action writes a ledger entry.
- Add no new outbound network path. Nothing phones home.
- Never modify a bundled third-party service.

## 8. How to write code
- The simplest solution that works. Reuse what exists. Match the surrounding
  style and naming.
- Add a general mechanism only when two packs need it.
- Tests first for logic: branches, parsers, transforms, money, auth,
  security. Keep tests minimal, and show the test fails without the change.
- Comments explain why, not what. No commented-out code. Every `TODO` carries
  an issue number.
- Personas and prompts are code. Follow `docs/architecture/personas.md`, bump
  the version, and run `just persona-eval` before opening the PR.

## 9. Verify, then report honestly
- Run `just check`, and `just e2e` when behaviour changes, before saying a
  task is done.
- Report the exact commands you ran and their actual results. If something
  failed or you skipped it, say so plainly.
- Never invent results, benchmarks, file contents, API behaviour, citations
  or licence facts. If you're not sure, write "unverified".
- If code and docs disagree, the code is the truth: fix the docs and note the
  discrepancy.

## 10. Document every change
- Add one work-log entry with `just new-doc log <branch-name>`. Fill every
  section, including the exact verification commands and their results.
- Update every docs page whose `covers` paths you touched. Write an ADR for
  any design decision.
- Follow the docs rules: frontmatter, relative links, one page per subject.
- Commit docs on the same branch as the code they describe. A docs-only fix
  (a wrong fact, a broken link) gets its own small `docs/<topic>` PR straight
  away.

## 11. Commits, pushing and pull requests
- Commit after every finished step: the failing test, the code that passes
  it, a refactor, a docs page, the log entry, each review fix. Small commits
  (under about 100 lines), each one working, each doing one thing.
- Never pad: no empty commits, no whitespace-only churn, no splitting one
  change artificially.
- Conventional Commits, scoped to the package or pack:
  `feat(rules): add authority rule type`.
- Stage only your own paths (`git add <path>`), never everything at once.
- Push your branch to GitHub after every finished step, and always before you
  stop working. Nothing, docs included, stays only on your machine.
- Open a draft PR after your first push, from the template and linked to its
  issue, so the team can see the work and its log entry. Mark it ready for
  review when `just check` passes. Keep it under about 400 changed lines.
- Docs reach `4ce-core` only through a merged PR. Never push to `4ce-core`.
- No tool attribution anywhere: no tool co-author trailers, no "generated by"
  lines. The person who opens the PR is the author.
- Commit as the human you're working for, with their verified GitHub email,
  so every commit counts on their profile.

## 12. Working alongside others
- Another person or agent may be working at the same time. Check `git status`
  and `git diff` before editing a file.
- Never revert, stash, overwrite or reformat changes you didn't make.
- One agent per branch.

## 13. Stop and ask a human when
- the requirements are unclear or contradict each other
- a rule here blocks the task
- a check fails for a reason outside your work package
- the change touches policy, the ledger, sign-off, the sandbox or pack signing
- a licence or security question comes up
- the next step can't be undone

## Where the details live
- Repository layout, naming and working rules: `docs/architecture/repository.md`
- Documentation rules: `docs/architecture/documentation.md`
- Architecture: `docs/architecture/overview.md`
- Current state: `docs/state.md`
