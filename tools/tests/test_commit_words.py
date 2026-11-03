from pathlib import Path

import commit_words
import pytest

# Stand-ins: the real lists are digests of words this file must not contain either.
TERMS = ["widget"]
LISTS = {
    "refused": {commit_words.digest("acme"), commit_words.digest("acmes")},
    "numbered": {commit_words.digest("step")},
    "openings": {commit_words.digest("made with")},
    "allowed": {commit_words.digest("acme out"), commit_words.digest("query acme")},
}


def problems(message: str) -> list[str]:
    return commit_words.check_message(message, TERMS, **LISTS)


def test_a_plain_message_passes() -> None:
    message = "feat(storage): add the local file store\n\nWrites go to a part file first.\n"
    assert problems(message) == []


def test_a_neutrality_term_is_refused_in_the_subject_and_the_body() -> None:
    assert problems("fix(jobs): widgets in the queue") == ["commit message:1: 'widget'"]
    assert problems("fix(jobs): x\n\nA Widget here.") == ["commit message:3: 'widget'"]


def test_a_refused_word_is_found_in_any_case_and_inside_punctuation() -> None:
    assert problems("docs: the Acme's notes") == ["commit message:1: 'acme'"]
    assert problems("docs: (ACMES)") == ["commit message:1: 'acmes'"]
    assert problems("docs: acmexyz and xacme pass") == []  # whole words only


def test_a_word_refused_before_a_number_passes_otherwise() -> None:
    assert problems("docs: as in Step 12b") == ["commit message:1: 'step 12b'"]
    assert problems("docs: step by step") == []


def test_an_attribution_opening_is_refused_only_at_the_start_of_a_line() -> None:
    assert problems("feat: x\n\nMade with something") == ["commit message:3: 'made with'"]
    assert problems("feat: a key made with care") == []


def test_allowed_phrases_keep_a_refused_word() -> None:
    assert problems("docs: acme out a race; the query acme") == []


def test_a_teammates_co_author_trailer_passes() -> None:
    assert problems("feat: x\n\nCo-authored-by: Pranay <pranay@example.com>") == []


def test_comments_and_everything_below_the_scissors_are_ignored() -> None:
    message = (
        "feat: x\n# acme in a comment\n"
        "# ------------------------ >8 ------------------------\nacme widget\n"
    )
    assert problems(message) == []


def test_the_real_lists_hold_digests_and_pass_an_ordinary_message() -> None:
    for each in (
        commit_words.REFUSED,
        commit_words.NUMBERED,
        commit_words.OPENINGS,
        commit_words.ALLOWED,
    ):
        assert each and all(len(item) == 64 and int(item, 16) >= 0 for item in each)
    message = "fix(server): close the store after the database\n\nRuns in a finally block."
    assert commit_words.check_message(message, []) == []


def test_main_prints_each_problem_and_exits_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("docs: fix a link\n", encoding="utf-8")
    assert commit_words.main([str(path)]) == 0
    terms = commit_words.neutrality_check.load_terms(
        commit_words.neutrality_check.TERMS_FILE.read_text(encoding="utf-8")
    )
    path.write_text(f"docs: {terms[0]}\n", encoding="utf-8")
    assert commit_words.main([str(path)]) == 1
    printed = capsys.readouterr().out
    assert "commit message:1:" in printed and "AGENTS.md" in printed
