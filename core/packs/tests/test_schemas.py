import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.protocols import Validator

from fource.packs import SCHEMAS, schema

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST: dict[str, Any] = yaml.safe_load((FIXTURES / "pack.yaml").read_text(encoding="utf-8"))
RULE_PACK: dict[str, Any] = json.loads((FIXTURES / "rule-pack.json").read_text(encoding="utf-8"))


def validator(name: str) -> Validator:
    return Draft202012Validator(schema(name))


def errors(name: str, document: dict[str, Any]) -> list[str]:
    return [error.message for error in validator(name).iter_errors(document)]


@pytest.mark.parametrize("name", SCHEMAS)
def test_each_schema_is_valid_json_schema(name: str) -> None:
    Draft202012Validator.check_schema(schema(name))


def test_unknown_schema_name_is_an_error() -> None:
    with pytest.raises(ValueError):
        schema("nonsense")


def test_a_full_manifest_is_valid() -> None:
    assert errors("pack", MANIFEST) == []


def test_a_minimal_manifest_is_valid() -> None:
    minimal = {
        key: MANIFEST[key]
        for key in ("id", "title", "version", "kind", "risk_tier", "summary", "locales")
    }
    assert errors("pack", minimal) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "Example_Sector"),
        ("version", "1.0"),
        ("kind", "industry"),
        ("risk_tier", 4),
        ("contents", {"unknown": "x/"}),
    ],
)
def test_manifest_values_are_checked(field: str, value: object) -> None:
    broken = copy.deepcopy(MANIFEST) | {field: value}
    assert errors("pack", broken), field


def test_manifest_rejects_unknown_and_missing_fields() -> None:
    assert errors("pack", MANIFEST | {"colour": "blue"})
    without_tier = {k: v for k, v in MANIFEST.items() if k != "risk_tier"}
    assert errors("pack", without_tier)


def test_a_rule_pack_with_every_v1_rule_type_is_valid() -> None:
    assert errors("rule-pack", RULE_PACK) == []
    types = {rule["type"] for rule in RULE_PACK["rules"]}
    assert types == {"band", "expression", "enum", "presence", "date", "authority"}


def test_a_rule_pack_must_carry_tests() -> None:
    assert errors("rule-pack", RULE_PACK | {"tests": []})


def test_a_missing_reading_is_never_a_pass() -> None:
    assert errors("rule-pack", RULE_PACK | {"missing_reading": "PASS"})


def test_rules_are_checked_against_their_type() -> None:
    unknown = copy.deepcopy(RULE_PACK)
    unknown["rules"][0]["type"] = "guess"
    assert errors("rule-pack", unknown)
    bad_verdict = copy.deepcopy(RULE_PACK)
    bad_verdict["rules"][0]["bands"][0]["verdict"] = "MAYBE"
    assert errors("rule-pack", bad_verdict)
    no_clause = copy.deepcopy(RULE_PACK)
    del no_clause["rules"][1]["pass"]["clause"]
    assert errors("rule-pack", no_clause)


def test_rule_pack_ids_are_namespaced_by_their_pack() -> None:
    assert errors("rule-pack", RULE_PACK | {"pack": "example-rules"})
