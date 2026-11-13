"""A commit message says what changed, in the project's own words (AGENTS.md §11).

    uv run python tools/commit_words.py FILE     a commit message (the commit-msg git hook)

Refuses the sector terms of tools/neutrality-terms.txt (matched as the neutrality check
matches them), the words that describe how the work was organised rather than what changed,
tool names, and tool attribution lines. A teammate's Co-authored-by trailer is fine.

The refused words are kept as SHA-256 digests of their lower-case form, so that this check
names none of them itself. To see whether a word is refused, hash it the same way.
"""

import hashlib
import os
import re
import sys
from collections.abc import Collection
from pathlib import Path

import neutrality_check

# Refused anywhere: tool names, words for how the work was organised, and the forms of a
# neutrality term that its own pattern (plural only) does not reach.
REFUSED = frozenset(
    {
        "c857d09db23e6822e3600bc06ad8d58f92ed62bc8efd81c753f77048662cb97d",
        "c70eca6b0f88f44d81a41311647e50fda1ac454ec04ffd442b0eb4743a993131",
        "b225390a8984c8de4206c746772ab5ef2abb0a02bcb043da10f6d41c274d1a02",
        "c1472135b14c77c8bef98e73f70208325fa0dcf1e6bd668ae9b31a9cea295fe7",
        "98138992690303befcadad81902661622b4e9a46f7d22973a7f81d26298830ca",
        "244b8435061420f6b2887681bbe2d24b18fc8f790a75c5bf16937bb8417e651a",
        "8ee47f99b969e2fb568cbe25287172e75837e39eef6a5998a17e6637ab6fd774",
        "94a168d2da574b00ec6c787377278465271cf2b97e68af076fc3eee87eba8664",
        "d298391b07433318a02bd922ed5b90112a4302606c4928b54e3fb1c18130d92e",
        "d3d7ca6ce0ae2ceb8c67aa18d1f3f56f34006b316b0189ad23a3534c2d18f3e2",
        "eba5605ebdc53df3e9b9b31825f898cef18d5b52edc3c48cf20cd66626ced06e",
        "132a0519893f35d86aafbf5cd9863a34867ef0c6595f32fb2e1d8c1e1951fdc5",
        "33ecf0cd36997c870fbc768ca1dc6795fcde1fed7d83b83c6caded0d56efc2ac",
        "d79d3458a58877cd8e48c18ebaf4c27b9d5c1a9cb5dfbdac769a7a21d8a1022e",
        "c66ba91dbd824314a5aae3ca2d821d41746270f4f96e5a909c3dc549284bc317",
        "702592427b0731310a5be2d1c8c20ec7d09c449866401abde0f171797e6c70cc",
        "d9b1fe39e950ea353ff707d80597ffbc8a91add3e198c5cc4ccb83721716c403",
    }
)
# Refused when a number follows (a step of a plan, such as "<word> 12b").
NUMBERED = frozenset({"0ebb429fa86d481c2630fac53db1c91cffed5d4d41d1021c179444eb67e7ee0b"})
# Two words that start an attribution line (the subject, or a line after a blank line).
OPENINGS = frozenset(
    {
        "2e8aae79d9566c6391cbf216d0b40760bde9bd51a6c5b0b970a248f679cd718f",
        "8316b399af66208937f9fe28d70a160fa0d26060ab53df53cb5ab55c10eb4cfe",
    }
)
# Two-word phrases in which a refused word is plain English or a database term.
ALLOWED = frozenset(
    {
        "6ad19d0c692d647146f3c7e4e526012fd2bd77387085fe2ab02cad2a75eb9de1",
        "d665faede8cdf4b2bcfff34b51119b459af1039e5f85a4a545080e7ceceb1d23",
    }
)
WORD = re.compile(r"[a-z0-9]+")
STEP = re.compile(r"\d+[a-z]?")
SCISSORS = "# ------------------------ >8 ------------------------"
ADVICE = "Reword it: say what changed, in the project's own words (AGENTS.md §11)."


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def kept_lines(message: str, keep_comments: bool = False, /) -> list[str]:
    """What git keeps of a message: no comment lines, nothing below the scissors line.

    With `keep_comments` every line is kept: when no editor opens (`-m`, `-F`), git does not
    strip `#` lines or cut at the scissors line, so a refused word there would be stored."""
    if keep_comments:
        return message.splitlines()
    kept: list[str] = []
    for line in message.splitlines():
        if line.rstrip() == SCISSORS:
            break
        if not line.startswith("#"):
            kept.append(line)
    return kept


def _allowed(words: list[str], at: int, allowed: Collection[str]) -> bool:
    before = at > 0 and digest(f"{words[at - 1]} {words[at]}") in allowed
    after = at + 1 < len(words) and digest(f"{words[at]} {words[at + 1]}") in allowed
    return before or after


def check_line(
    line: str,
    opens: bool = True,
    /,
    *,
    refused: Collection[str] = REFUSED,
    numbered: Collection[str] = NUMBERED,
    openings: Collection[str] = OPENINGS,
    allowed: Collection[str] = ALLOWED,
) -> list[str]:
    """The refused words of one line, as written there (lower case). An attribution opening
    counts only where `opens` (the subject, or the first line of a paragraph): inside a
    wrapped sentence the same two words are ordinary English."""
    words = WORD.findall(line.lower())
    found: list[str] = []
    if opens and len(words) > 1 and digest(f"{words[0]} {words[1]}") in openings:
        found.append(f"{words[0]} {words[1]}")
    for at, word in enumerate(words):
        if digest(word) in refused and not _allowed(words, at, allowed):
            found.append(word)
        elif digest(word) in numbered and at + 1 < len(words) and STEP.fullmatch(words[at + 1]):
            found.append(f"{word} {words[at + 1]}")
    return found


def check_message(
    message: str, terms: list[str], keep_comments: bool = False, /, **lists: Collection[str]
) -> list[str]:
    """Every problem with a commit message, one line each; `keep_comments` is true when git
    keeps the `#` lines; `lists` replaces the digests (tests use their own, so that they
    name no refused word either)."""
    lines = kept_lines(message, keep_comments)
    problems = neutrality_check.find_terms("commit message", "\n".join(lines), terms)
    for number, line in enumerate(lines, start=1):
        opens = number == 1 or not lines[number - 2].strip()
        problems += [
            f"commit message:{number}: '{word}'" for word in check_line(line, opens, **lists)
        ]
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    terms = neutrality_check.load_terms(neutrality_check.TERMS_FILE.read_text(encoding="utf-8"))
    # Git runs the hook with GIT_EDITOR=":" when no editor opens, and keeps '#' lines then.
    keep_comments = os.environ.get("GIT_EDITOR") == ":"
    problems = check_message(Path(argv[0]).read_text(encoding="utf-8"), terms, keep_comments)
    for problem in problems:
        print(problem)
    if problems:
        print(ADVICE)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
