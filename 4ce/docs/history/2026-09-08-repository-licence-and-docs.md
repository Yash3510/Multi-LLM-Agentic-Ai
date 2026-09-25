---
title: Repository layout, licence and public documents
type: git-history
status: historical
date: 2026-09-08
commits: [bdc4ac3, 1751dd7, 8e6d22e, 8b92f73, f8942ca, b790175, 0bc341d, 27b5c43, 057184d, 08d8184, 51897ef, c36baee, 553e592, badd4de, fb20d89, ad1becd]
authors: [Yash Kumar Singh, grizzly077, rituraj thakur]
tags:
  - 4ce
  - git-history
---

# Repository layout, licence and public documents

## Commits

| Commit | Date | Author | Subject |
|---|---|---|---|
| `bdc4ac3` | 2026-09-08 | Yash Kumar Singh | Cross-link the upstream README and research notes to the 4CE layer |
| `1751dd7` | 2026-09-10 | grizzly077 | Add HOW_TO_RUN.md with local setup and run instructions for 4CE |
| `8e6d22e` | 2026-09-10 | grizzly077 | Present the repo as 4CE and commit the backend branding |
| `8b92f73` | 2026-09-11 | rituraj thakur | Readme update |
| `f8942ca` | 2026-09-13 | rituraj thakur | Fix formatting and update README content |
| `b790175` | 2026-09-13 | rituraj thakur | Remove unnecessary smiley from README |
| `0bc341d` | 2026-09-13 | Yash Kumar Singh | Group the 4CE material so it is separable from upstream |
| `27b5c43` | 2026-09-13 | Yash Kumar Singh | Add the repository metadata a reader actually needs |
| `057184d` | 2026-09-16 | rituraj thakur | Remove Attribution and licence section from README |
| `08d8184` | 2026-09-16 | rituraj thakur | Readme update |
| `51897ef` | 2026-09-18 | Yash Kumar Singh | Correct the verification table against what actually ran |
| `c36baee` | 2026-09-18 | Yash Kumar Singh | Point the contents list at sections that exist |
| `553e592` | 2026-09-20 | Yash Kumar Singh | Carry the Obsidian vault settings with the repository |
| `badd4de` | 2026-09-20 | rituraj thakur | read me update |
| `fb20d89` | 2026-09-20 | rituraj thakur | Delete LICENSE |
| `ad1becd` | 2026-09-24 | Yash Kumar Singh | Restore the upstream licence text |

`ad1becd`'s subject names the upstream project; it is shortened here.

## Summary

The README became 4CE's own. Everything the project wrote moved under `4ce/`,
with the documentation under `4ce/docs/`. Community health files were added,
and the licence file was deleted and then restored.

## Why it changed

- A reader could not tell which of about forty root files were the project's
  own (`0bc341d`).
- The public page was missing a security statement, contribution notes and a
  citation file (`27b5c43`).
- The verification table had drifted from what had actually been run: one row
  under-claimed and one over-claimed (`51897ef`).
- `LICENSE_NOTICE` still pointed to `LICENSE` after that file was emptied and
  deleted. Clause 1 of the licence requires redistributions of source to keep
  the copyright notice (`ad1becd`).

## Files changed

- `README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CITATION.cff`, `LICENSE`
- `4ce/docs/` (created by the moves in `69df476` and `0bc341d`)
- `.obsidian/` (vault settings, `553e592`)

## Technical changes

- **README** (`8e6d22e`, then edits by rituraj thakur). Replaced with a 4CE
  README covering the chain, the sovereignty properties, a quick start and the
  verification status. Later edits removed the attribution and contributing
  sections (`8b92f73`, `057184d`, `08d8184`), and `c36baee` removed the
  contents entries they left pointing nowhere.
- **Layout** (`0bc341d`). Documentation under `4ce/docs/`, images beside it.
  Executable paths were left alone, and every relative link was re-checked.
- **Metadata** (`27b5c43`). `SECURITY.md` states the limits of the
  sovereignty claim rather than assurances. `CONTRIBUTING.md` explains the
  `ace_*` plugin ids. `CITATION.cff` was added.
- **Run guide** (`1751dd7`). `HOW_TO_RUN.md`, first written for a conda
  environment on macOS.
- **Obsidian vault settings** (`553e592`). Filters that leave only the project's
  documents visible, out of more than 117,000 files in the tree.
- **Licence** (`badd4de` emptied `LICENSE`, `fb20d89` deleted it, and
  `ad1becd` restored the original 2,819 bytes unchanged).

## Impact

No runtime behaviour changed. `LICENSE` was missing from the tree between
`fb20d89` and `ad1becd` (2026-09-20 to 2026-09-24).

## Related documentation

- [Docs index](../README.md)
- [Timeline](README.md)
