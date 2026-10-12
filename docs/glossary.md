---
title: Glossary
type: glossary
status: active
owner: R1
updated: 2026-10-12
tags: [4ce, glossary]
---

# Glossary

Every 4CE term, one definition each. Other pages link here instead of redefining a term.

| Term | Meaning |
| --- | --- |
| **4CE Linux runtime** | The one Linux environment the 4CE stack runs in on every host: a WSL2 distribution on Windows, a Lima VM on macOS, the machine itself on the appliance |
| **AGENTS.md** | The one file of rules every coding agent follows in this repository, whatever the tool |
| **Assessment** | Rule verdicts over observations, with clauses and the pack hash |
| **Assured run** | One request taken through the full loop: read, rules, verification, sign-off and ledger |
| **Canonical page** | The one docs page that owns a subject; every other page links to it instead of repeating it |
| **Case** | A subject's history over time |
| **Cross-sector pack** | A pack for a function every organisation has, e.g. Procurement, Contracts |
| **Deep Cache** | Representations of a document computed once at ingest and reused for every question |
| **Docs drift check** | The CI check that fails a PR that changes code under a page's `covers` paths without updating that page |
| **Document kind** | A pack-defined type of evidence, with how to recognise it and what to read from it |
| **Evidence pack** | A zip anyone can verify offline: deliverable, ledger slice, pack hashes, models, verification report and verifier |
| **Fingerprint** | The SHA-256 of exactly the text that was approved and released |
| **Import scan** | The CI check that fails if 4CE code imports a copyleft or source-available library without a commercial licence |
| **Installer engine** | 4CE's own installer logic: a list of steps, each with a check and an apply, so running it again repairs or upgrades and never duplicates |
| **Ledger checkpoint** | A signed snapshot of the ledger's chain head |
| **Model qualification** | The eval run that decides which roles a model may take; the router follows it |
| **Neutrality check** | The CI check that keeps sector vocabulary out of core code |
| **Observation** | A value with unit and provenance, read from evidence or entered |
| **Pack** | A signed bundle that teaches the core one industry or one department: vocabulary, document kinds, rules, calculators, workflows, templates, policies, evals |
| **Pack Studio** | The no-code tool where domain experts author and test packs |
| **Persona** | The versioned role prompt every model call goes through: a core layer, a pack layer and a model layer, compiled per call |
| **Profile** | A hardware tier with its models, context sizes and budgets |
| **Prompt profile** | A registry field describing how a model must be prompted: size class, structured-output support, thinking switch, effective context, known issues |
| **Repo check** | The CI check that keeps the repository neat: allowed root files, folder and file naming, banned names, file sizes, a README and tests per package, uv-only dependency files |
| **Risk tier** | A pack's declared stakes (1 office, 2 financial and legal, 3 safety and life), which set defaults packs can't loosen |
| **Rule of two** | A general mechanism is added to the core only when two packs need it |
| **Rule pack** | A signed, tested set of authored rules with clause references, run by the Rule Engine. One pack can contain several rule packs. |
| **Sector pack** | A pack for one industry, e.g. Industrial & Energy, Banking & Lending |
| **Seeded fault** | An error planted on purpose to measure whether verification catches it |
| **Skill** | A small installable bundle of know-how for one kind of task (instructions, plus optional scripts and resources) in the open skill format |
| **Skill guidance** | A matched skill's instructions, placed in a persona for one call, labelled as unable to override the rules above it |
| **Subject** | The thing a decision is about: an asset, an application, a claim, a batch |
| **Third-party bundle** | The licence, notices, version and source of every bundled service, shipped with each appliance image and update |
| **Two-pack test** | The end-to-end suite run against two unrelated packs on the same build |
| **Work log** | One `docs/log/` entry per merged PR: what changed, why, the files, how it was verified, the decisions, the follow-ups |
