# fource-packs

The pack system: how a pack declares itself and how it authors rules. Today it publishes the two draft specs (WP-PK-01); the loader, validator, namespacing, signing and activation follow in WP-PK-02 and WP-PK-03.

**Owner:** R1

## Public API

| Name | What it is |
| --- | --- |
| `SCHEMAS` | The schema names: `pack` and `rule-pack` |
| `schema(name)` | The JSON Schema (draft 2020-12) for a pack manifest (`pack.yaml`) or a rule pack |

```python
from jsonschema import Draft202012Validator
from fource.packs import schema

Draft202012Validator(schema("rule-pack")).validate(rule_pack)
```

## The specs (draft 1)

- **Pack manifest** ([`pack.schema.json`](src/fource/packs/schemas/pack.schema.json)): id, title, semantic version, kind (`sector` or `cross`), risk tier, summary, locales, dependencies with version ranges, minimum profile, subjects and roles with per-locale labels, the content folders it ships, signed code, and signatures. Signatures may be absent while authoring; activation will require them.
- **Rule Pack** ([`rule-pack.schema.json`](src/fource/packs/schemas/rule-pack.schema.json)): the rulebook it cites (clause references and limits, never its text), author, approver, effective date, parameters with units, rules, the verdict for a missing reading (never `PASS`), and tests (at least one). Rule types: `band`, `enum`, `presence` / `absence`, `expression`, `date` and `authority`, each with an exact shape; every outcome names its clause.

Decided in ADR-0012 and ADR-0019 (both to be written with WP-PK-02). Open points are listed in [the work log](../../docs/log/README.md).

## Tests

```
uv run pytest core/packs
```
