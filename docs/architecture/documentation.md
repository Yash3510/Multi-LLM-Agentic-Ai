---
title: Documentation rules
type: architecture
status: active
owner: R1
updated: 2026-10-12
covers:
  - docs/templates/
  - .obsidian/
  - tools/docs_check.py
tags: [4ce, architecture, documentation]
---

# Documentation rules

`docs/` is the project's memory. A new teammate, a reviewer, an auditor or a pilot customer must be able to answer "what does this do, why is it built this way, what changed, and what's true right now?" from `docs/` alone.

## Principles

1. **One home per subject.** Every subject has exactly one canonical page. Other pages link to it and never repeat it. If two pages cover the same thing, one is merged into the other in the same week.
2. **Docs describe committed code, and nothing else as fact.**
   - Planned work is labelled `planned`.
   - An untested claim is labelled `unverified`.
   - A measurement names its commit, date, environment and the command that produced it.
   - Nothing is called verified without evidence someone can rerun.
3. **The same PR changes code and docs together.**
4. **Every change leaves a record:** one work-log entry per PR, written in that PR.
5. **Capture, organise, distil.** Log entries capture each change; history pages organise them into milestones; the state page, the changelog and the index distil them.
6. **Human knowledge is preserved.** Research and meeting notes are kept and labelled by type. A page is never deleted to tidy up: it is marked `deprecated` or `historical`, with a link to what replaced it.
7. **The docs live on GitHub, not on laptops.** `main` on GitHub is the knowledge base everyone reads.

## The vault

- **The repository root is the Obsidian vault.**
- **`.obsidian/` commits only shared settings.** `app.json` hides the source trees so search and the graph show only the knowledge base and keeps links relative; `core-plugins.json` enables only core plugins (Templates, Properties, Backlinks, Graph and Bases); `templates.json` points Templates at `docs/templates/`. Per-person files are git-ignored.
- **No community plugins are required.** Everything renders in plain Obsidian and on GitHub.
- **Links are relative markdown links,** such as `[Repository](repository.md)`, never `[[wikilinks]]`, so they work in Obsidian and on GitHub. Section links use heading anchors.

## Layout

| Path | Holds |
| --- | --- |
| [`README.md`](../README.md) | The index: "start here", then every page with its type and status, and the tag list |
| [`state.md`](../state.md) | What works today, what's in progress, open questions, next up |
| [`glossary.md`](../glossary.md) | Every 4CE term, one definition each |
| [`architecture/`](README.md) | One canonical page per subsystem, plus the overview |
| [`adr/`](../adr/README.md) | Decision records, `NNNN-kebab-title.md` |
| [`packs/`](../packs/README.md) | The pack authoring guide, spec reference, one page per pack |
| [`skills/`](../skills/README.md) | The skill authoring guide, format reference, one page per built-in skill |
| [`testing/`](../testing/README.md) | Strategy, eval methods, measured results |
| [`runbooks/`](../runbooks/README.md) | Install, upgrade, backup and restore, release, incident response |
| [`log/`](../log/README.md) | The work log: `log/YYYY/MM/YYYY-MM-DD-<branch-name>.md`, one entry per PR |
| [`history/`](../history/README.md) | Milestone pages and the timeline |
| [`research/`](../research/README.md) | Studies, spikes, competitor notes, meeting notes |
| [`assurance/`](../assurance/README.md) | Published Assurance Reports, `assurance/<version>/` |
| [`templates/`](../templates/README.md) | One template per page type |

File names are kebab-case and every folder has a `README.md` index. New pages start from a template in `docs/templates/` (Obsidian's Templates plugin reads that folder).

## Frontmatter

Every page starts with:

```yaml
---
title: Rule Engine
type: architecture        # controlled list below
status: active            # controlled list below
owner: R1                 # the role that keeps it true: R1, R2, R3 or R4
updated: 2026-11-02       # the date of the last real change
covers:                   # code paths this page describes; drives the drift check
  - core/rules/
tags: [4ce, architecture, rules]
---
```

| Field | Allowed values |
| --- | --- |
| `type` | `index`, `state`, `glossary`, `architecture`, `adr`, `pack`, `testing`, `runbook`, `log`, `history`, `research`, `assurance`, `template` |
| `status` | `active`, `implemented`, `experimental`, `planned`, `deprecated`, `historical`, `unverified` |
| `tags` | From the fixed list in [`docs/README.md`](../README.md#tags) only. A new tag needs a PR to that list. |

`covers` is optional: pages that describe no code (the glossary, research notes) leave it out.

Some types need extra fields:

| Type | Extra fields |
| --- | --- |
| `adr` | `number`, `decision_status` (`proposed` / `accepted` / `superseded`), `superseded_by` |
| `log` | `date`, `branch`, `pr`, `work_package`, `author`, `areas` |
| `history` | `commits` (every commit hash on the page) |
| `testing` result | `commit`, `date`, `environment` |
| `history/README.md` | `last_processed_commit` |

## The work log

Every PR adds exactly one entry, `docs/log/YYYY/MM/YYYY-MM-DD-<branch-name>.md`, from [the log template](../templates/log.md). It records what changed, why, the files, how it was verified (the exact commands and their actual results; "tests pass" on its own is not accepted), the decisions, the docs updated, and the known limits, each linked to an issue.

## History, state and changelog

- **History** groups commits into milestone pages named `YYYY-MM-DD-title.md`, written from the diffs. Every commit appears in exactly one milestone. `history/README.md` holds the timeline and `last_processed_commit`, so the next update starts at `git log --reverse <last_processed_commit>..HEAD`. Updated weekly and at every milestone.
- **State** (`docs/state.md`) answers "where are we?". It is updated at the weekly planning and at every milestone, and goes stale after 7 days.
- **The changelog** (`CHANGELOG.md`) is the user-facing summary per release, generated from commits at release time.

## Decision records

- **Template:** Context · Decision · Alternatives considered · Consequences · Status.
- **Written in the same PR** that makes the decision real.
- **Never edited after acceptance,** except to set `superseded_by`. A changed decision is a new ADR.
- **Listed in [`adr/README.md`](../adr/README.md)** and linked from the architecture page it affects.

## Keeping everyone current

- **Push as you go,** and open a draft PR after the first push.
- **Docs reach `main` only through merged PRs.**
- **Docs-only fast lane:** a PR that changes only `docs/` needs one approval, from the owner of the pages it touches, and is merged the same day.
- **Pull before you start** with `just sync`.

## The docs check

[`tools/docs_check.py`](../../tools/docs_check.py) runs in `just check` (`just docs`). The PR rules (work log, drift, ADRs) need the branch the PR targets: `just docs --base origin/main`, plus `--allow-drift` only when the PR carries the `docs-unaffected` label. It fails when:

| Check | Fails when |
| --- | --- |
| Frontmatter | A page misses a required field, or uses a type, status or tag outside the lists |
| Links | A relative link or heading anchor doesn't resolve |
| Orphans | A page isn't reachable from `docs/README.md` |
| Names | A file breaks the naming or banned-name rules |
| Work log | A PR has no log entry, or more than one |
| Drift | Code under a page's `covers` changed but the page didn't. The only override is the `docs-unaffected` label, approved by the page owner. |
| History | A commit up to `last_processed_commit` is in no milestone, or in more than one |
| State | `docs/state.md` is more than 7 days old |
| ADRs | An accepted ADR's body was edited |

## Definition of "documented"

A change is documented when its log entry exists, every page describing the touched code is updated, any decision has an ADR, the index lists any new page, and the docs check is green.

## Decisions

[ADR-0031](../adr/0031-documentation-knowledge-base.md).
