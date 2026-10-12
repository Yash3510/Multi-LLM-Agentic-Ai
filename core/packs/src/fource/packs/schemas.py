import json
from importlib.resources import files
from typing import Any

SCHEMAS = ("pack", "rule-pack")


def schema(name: str) -> dict[str, Any]:
    """The published JSON Schema (draft 2020-12) for a pack manifest or a rule pack."""
    if name not in SCHEMAS:
        raise ValueError(f"no schema named '{name}'; the schemas are {', '.join(SCHEMAS)}")
    text = files("fource.packs").joinpath("schemas", f"{name}.schema.json").read_text("utf-8")
    loaded: dict[str, Any] = json.loads(text)
    return loaded
