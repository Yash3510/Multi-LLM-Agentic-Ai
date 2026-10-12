from typing import Any

import licence_gate


def component(name: str, version: str, *licences: str) -> dict[str, Any]:
    entries = [
        {"expression": text} if " OR " in text or " AND " in text else {"license": {"id": text}}
        for text in licences
    ]
    return {"name": name, "version": version, "licenses": entries}


def test_allowed_licences_pass() -> None:
    for expression in ("MIT", "BSD-3-Clause", "Apache-2.0 OR BSD-2-Clause", "PSF-2.0"):
        assert licence_gate.problem(expression) == "", expression


def test_every_option_of_an_expression_must_be_allowed() -> None:
    assert "GPL-3.0-only" in licence_gate.problem("MIT OR GPL-3.0-only")
    assert "MPL-2.0" in licence_gate.problem("(MIT AND MPL-2.0)")


def test_review_denied_and_unknown_licences_fail_with_a_reason() -> None:
    assert "review" in licence_gate.problem("MPL-2.0")
    assert "denied" in licence_gate.problem("AGPL-3.0-only")
    assert "denied" in licence_gate.problem("SSPL-1.0")
    assert "not a licence the policy names" in licence_gate.problem("BSD License")


def test_lgpl_needs_review_but_is_not_denied() -> None:
    assert not licence_gate.denied("LGPL-2.1-only")
    assert licence_gate.denied("MIT OR GPL-2.0-only")


def test_components_are_checked_and_our_own_packages_skipped() -> None:
    components = [
        component("ruff", "0.17.0", "MIT"),
        component("fource-common", "0.1.0"),
        component("some-lib", "1.0", "GPL-2.0-only"),
        component("bare", "2.0"),
    ]
    problems = licence_gate.check_components(components, reviewed={})
    assert len(problems) == 2
    assert any(p.startswith("some-lib 1.0:") for p in problems)
    assert any(p.startswith("bare 2.0:") and "no licence" in p for p in problems)


def test_a_reviewed_licence_applies_only_to_the_version_that_was_read() -> None:
    reviewed = {("grimp", "3.17"): "BSD-2-Clause"}
    assert (
        licence_gate.check_components([component("grimp", "3.17", "BSD License")], reviewed) == []
    )
    problems = licence_gate.check_components([component("grimp", "3.18", "BSD License")], reviewed)
    assert problems and "grimp 3.18" in problems[0]


def test_a_commercially_licensed_library_passes() -> None:
    problems = licence_gate.check_components(
        [component("PyMuPDF", "1.26.0", "AGPL-3.0-or-later")], reviewed={}
    )
    assert problems == []


def test_reviewed_file_is_read_into_name_and_version() -> None:
    text = """
[[package]]
name = "nodeenv"
version = "1.11.0"
licence = "BSD-3-Clause"
checked = "LICENSE file in the wheel, 2026-10-12"
"""
    assert licence_gate.load_reviewed(text) == {("nodeenv", "1.11.0"): "BSD-3-Clause"}
