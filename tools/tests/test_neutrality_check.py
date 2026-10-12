import neutrality_check

TERMS = neutrality_check.load_terms(
    """
    # comments and blank lines are ignored

    pump
    seal leak
    P&ID
    loan
    """
)


def found(path: str, text: str) -> list[str]:
    return neutrality_check.find_terms(path, text, TERMS)


def test_term_list_ignores_comments_and_blank_lines() -> None:
    assert TERMS == ["pump", "seal leak", "P&ID", "loan"]


def test_reports_path_line_and_term() -> None:
    assert found("core/rules/src/fource/rules/engine.py", "x = 1\nlimit = pump_limit\n") == [
        "core/rules/src/fource/rules/engine.py:2: 'pump'"
    ]


def test_matches_whatever_the_identifier_style() -> None:
    for text in ("Pumps", "PumpCurve", "max_pump", "seal_leak", "SealLeak", "seal-leak", "P&ID"):
        assert found("core/x.py", text), text


def test_ignores_words_that_merely_contain_a_term() -> None:
    for text in ("pumpkin", "sloan", "seal leaky", "P&IDE"):
        assert found("core/x.py", text) == [], text


def test_file_and_folder_names_count_too() -> None:
    assert found("core/rules/src/fource/rules/pump.py", "") == [
        "core/rules/src/fource/rules/pump.py: 'pump' in the path"
    ]
