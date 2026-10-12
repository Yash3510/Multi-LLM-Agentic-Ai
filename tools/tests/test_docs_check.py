from datetime import date

import docs_check

INDEX = """---
title: Index
type: index
status: active
owner: R1
updated: 2026-10-12
tags: [4ce, index]
---

# Index

- [Rules](architecture/rules.md)
- [State](state.md)

## Tags

- `4ce`
- `index`
- `architecture`
- `state`
"""

RULES = """---
title: Rule Engine
type: architecture
status: active
owner: R1
updated: 2026-10-12
covers:
  - core/rules/
tags: [4ce, architecture]
---

# Rule Engine

See [the state](../state.md#what-works) and [the code](../../core/rules/README.md).

## Band rules

```
[not a link](nowhere.md)
```

Inline `[not a link](nowhere.md)` either.
"""

STATE = """---
title: State
type: state
status: active
owner: R1
updated: 2026-10-10
tags: [4ce, state]
---

# State

## What works

Back to the [index](README.md) and [band rules](architecture/rules.md#band-rules).
"""


def docs(**overrides: str) -> dict[str, str]:
    pages = {
        "docs/README.md": INDEX,
        "docs/architecture/rules.md": RULES,
        "docs/state.md": STATE,
    }
    pages.update(overrides)
    return pages


def exists(path: str) -> bool:
    return path == "core/rules/README.md"


def test_a_good_set_of_pages_passes() -> None:
    pages = docs()
    assert docs_check.check_frontmatter(pages) == []
    assert docs_check.check_links(pages, exists) == []
    assert docs_check.check_orphans(pages) == []
    assert docs_check.check_state(pages, today=date(2026, 10, 12)) == []


def test_tags_come_from_the_index() -> None:
    assert docs_check.allowed_tags(INDEX) == {"4ce", "index", "architecture", "state"}


def test_frontmatter_fields_and_values_are_checked() -> None:
    broken = RULES.replace("status: active", "status: done").replace("owner: R1\n", "")
    broken = broken.replace("tags: [4ce, architecture]", "tags: [4ce, misc]")
    problems = docs_check.check_frontmatter(docs(**{"docs/architecture/rules.md": broken}))
    assert any("status" in p and "done" in p for p in problems)
    assert any("owner" in p for p in problems)
    assert any("misc" in p for p in problems)


def test_a_page_without_frontmatter_fails() -> None:
    problems = docs_check.check_frontmatter(docs(**{"docs/state.md": "# State\n"}))
    assert problems == ["docs/state.md: no frontmatter"]


def test_types_need_their_extra_fields() -> None:
    adr = INDEX.replace("type: index", "type: adr").replace("title: Index", "title: X")
    problems = docs_check.check_frontmatter(docs(**{"docs/adr/0040-x.md": adr}))
    assert any("decision_status" in p for p in problems)
    assert any("number" in p for p in problems)


def test_templates_only_need_the_fields_not_real_values() -> None:
    template = RULES.replace("updated: 2026-10-12", 'updated: "{{date}}"')
    assert docs_check.check_frontmatter(docs(**{"docs/templates/architecture.md": template})) == []


def test_broken_links_and_anchors_are_found() -> None:
    page = STATE.replace("README.md)", "missing.md)").replace("#band-rules", "#nope")
    problems = docs_check.check_links(docs(**{"docs/state.md": page}), exists)
    assert any("missing.md" in p for p in problems)
    assert any("#nope" in p for p in problems)
    assert len(problems) == 2


def test_heading_anchors_follow_github() -> None:
    assert docs_check.slug("Dependencies: uv for everything Python") == (
        "dependencies-uv-for-everything-python"
    )
    assert docs_check.slug("ADR-0035: Frontend `foundations`") == "adr-0035-frontend-foundations"
    assert docs_check.slug("Where does it go?") == "where-does-it-go"


def test_pages_not_reachable_from_the_index_are_orphans() -> None:
    lonely = STATE.replace("title: State", "title: Lonely")
    problems = docs_check.check_orphans(docs(**{"docs/research/lonely.md": lonely}))
    assert problems == ["docs/research/lonely.md: not reachable from docs/README.md"]


def test_state_goes_stale_after_seven_days() -> None:
    assert docs_check.check_state(docs(), today=date(2026, 10, 17)) == []
    problems = docs_check.check_state(docs(), today=date(2026, 10, 18))
    assert problems and "docs/state.md" in problems[0]


def test_a_pr_adds_exactly_one_log_entry() -> None:
    assert docs_check.check_work_log(["docs/log/2026/10/2026-10-12-wp-x.md", "core/a.py"]) == []
    assert docs_check.check_work_log(["core/a.py"]) != []
    two = ["docs/log/2026/10/2026-10-12-a.md", "docs/log/2026/10/2026-10-13-a.md"]
    assert docs_check.check_work_log(two) != []


def test_changing_covered_code_needs_the_page_updated() -> None:
    pages = docs()
    problems = docs_check.check_drift(pages, ["core/rules/src/fource/rules/engine.py"])
    assert problems == [
        "docs/architecture/rules.md: covers core/rules/ which changed; update the page"
    ]
    changed = ["core/rules/src/fource/rules/engine.py", "docs/architecture/rules.md"]
    assert docs_check.check_drift(pages, changed) == []
    assert docs_check.check_drift(pages, ["core/calc/engine.py"]) == []


def test_every_processed_commit_is_in_exactly_one_milestone() -> None:
    history = INDEX.replace("type: index", "type: history").replace("tags: [4ce, index]", "")
    one = history.replace("title: Index", "title: One\ncommits: [aaaa111, bbbb222]")
    two = history.replace("title: Index", "title: Two\ncommits: [bbbb222]")
    pages = docs(**{"docs/history/2026-10-01-one.md": one, "docs/history/2026-10-09-two.md": two})
    processed = ["aaaa1111111", "bbbb2222222", "cccc3333333"]
    problems = docs_check.check_history(pages, processed)
    assert any("bbbb222" in p and "more than one" in p for p in problems)
    assert any("cccc333" in p and "no milestone" in p for p in problems)
    assert not any("aaaa111" in p for p in problems)


ACCEPTED = """---
title: Own core
type: adr
status: active
owner: R1
updated: 2026-10-12
tags: [4ce, adr]
number: 9
decision_status: accepted
superseded_by: null
---

# ADR-0009: Own core

We own every line.
"""


def test_accepted_adrs_are_never_edited() -> None:
    path = "docs/adr/0009-own-core.md"
    edited = ACCEPTED.replace("every line", "most lines")
    assert docs_check.check_adrs({path: edited}, {path: ACCEPTED}) != []
    superseded = ACCEPTED.replace("superseded_by: null", "superseded_by: 41").replace(
        "decision_status: accepted", "decision_status: superseded"
    )
    assert docs_check.check_adrs({path: superseded}, {path: ACCEPTED}) == []
    proposed = ACCEPTED.replace("accepted", "proposed")
    assert docs_check.check_adrs({path: edited}, {path: proposed}) == []
