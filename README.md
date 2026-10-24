# 4CE

**One engine. Any rulebook. Every answer proven.**

4CE is a self-hosted engine that turns an organisation's documents and rulebooks into decisions it can sign: grounded in its evidence, checked against its rules, approved by a named person, recorded as proof, and nothing leaves the building. The core is sector-neutral; each industry or department arrives as a pack.

The `4ce-core` branch of this repository is the owned rebuild, with its own history; the other branches hold the earlier fork it replaces. It is in Phase 0: the repository, its checks and the knowledge base exist; the product does not yet. [docs/state.md](docs/state.md) says what works today.

## Set up

You need [uv](https://docs.astral.sh/uv/) and git 2.38 or newer. Then:

```
uv tool install rust-just==1.58.0
git clone --branch 4ce-core https://github.com/Yash3510/Multi-LLM-Agentic-Ai.git 4ce
cd 4ce
just setup
just check
just dev
```

`just setup` installs Python 3.12, syncs every package and installs the git hooks. `just check` runs every check CI runs. `just dev` runs the server on http://127.0.0.1:8000; `just create-user you@example.com --role Admin` adds the first user. `just` on its own lists every command.

## Where things live

| Path | Holds |
| --- | --- |
| `core/` | The sector-neutral Python packages, one folder each |
| `apps/` | The server and the web UI (not built yet) |
| `packs/` | Industries and departments, mostly as configuration (not built yet) |
| `deploy/` | The bundled services, installers and third-party notices |
| `docs/` | The knowledge base, also an Obsidian vault: start at [docs/README.md](docs/README.md) |
| `tools/` | The repository's own checks and scaffolds, each run through `just` |

The full layout and the working rules are in [docs/architecture/repository.md](docs/architecture/repository.md). How to contribute is in [CONTRIBUTING.md](CONTRIBUTING.md); coding agents follow [AGENTS.md](AGENTS.md).
