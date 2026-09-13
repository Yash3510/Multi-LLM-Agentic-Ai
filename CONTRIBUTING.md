# Contributing

This repository is a fork. The distinction below matters more than any style rule:

- **`4ce/` is ours.** Change it freely.
- **Everything else is upstream's.** Change it only when there is no way to achieve
  the result from `4ce/`, and say why in the commit message. Every edit outside
  `4ce/` is a future merge conflict.

Most work belongs in `4ce/`, because the upstream plugin runtime is genuinely
capable: a function registers itself as a selectable model and owns a whole turn,
and tools are called by the agent chain. Neither requires touching upstream code.

## Setup

Node 22 and Python 3.11 are both required — Node 26 is blocked by the repository's
`engine-strict`, and the backend pins `>=3.11,<3.13`.

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv -r backend/requirements.txt
npm ci
cp 4ce/env.sovereign.example .env && cp .env backend/.env
```

Run the backend from `backend/`, the frontend with `npx vite dev`, then deploy the
plugin set:

```bash
python 4ce/install.py
```

Full instructions, including the model server, are in
[`4ce/docs/HOW_TO_RUN.md`](4ce/docs/HOW_TO_RUN.md).

## Adding a plugin

Add the file under `4ce/functions/` or `4ce/tools/`, then register it in the
`FUNCTIONS` or `TOOLS` list in [`4ce/install.py`](4ce/install.py) and re-run the
installer. The id must be a valid Python identifier — the upstream API rejects
anything else, which is why the ids are `ace_*` rather than `4ce_*`.

Tools are chosen by the model from their docstring, so write the docstring for
the caller: say when to use it and when not to.

## Tests

```bash
cd backend && ../.venv/Scripts/python.exe ../4ce/test_tools.py
```

It exercises each tool through its success *and* failure paths and exits non-zero
on failure. Docker must be running or the sandbox checks fail.

Add cases for boundaries rather than the happy path. The threshold engine is
tested at exactly 5 and exactly 20 drops per minute, and at a wall thickness
exactly equal to the retirement thickness, because those are where a rule is
either right or quietly wrong.

## What a change should keep true

- **Nothing reaches the network.** If a change introduces an outbound call, it has
  broken the product's only real claim. Run the sovereignty tool.
- **Nothing claims an action it did not perform.** Tools report failure plainly —
  the sandbox says it could not execute rather than implying it did.
- **The approval gate fails closed.** Anything ambiguous withholds the deliverable.
- **Verification stays independent.** ULTRON should run on a different model from
  JARVIS, or a model is grading its own work.

## Commits

Explain why the change was needed, not what the diff shows. Where a fix came from
observed behaviour, say what was observed — a note that the approval gate was
recording approvals nobody gave is worth more than a description of the patch.
