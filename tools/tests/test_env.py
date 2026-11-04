import re
from pathlib import Path

from dev import env

EXAMPLE = """# a comment with change-me in it stays
FOURCE_SECRET_KEY=change-me
FOURCE_POSTGRES_PASSWORD=change-me
# FOURCE_DATABASE_URL=postgresql+psycopg://fource_app:${FOURCE_POSTGRES_APP_PASSWORD}@localhost:5432/fource
FOURCE_ORG=default
"""


def counter() -> env.SecretMaker:
    numbers = iter(range(100))
    return lambda: f"secret-{next(numbers)}"


def test_every_placeholder_gets_its_own_secret() -> None:
    filled = env.fill(EXAMPLE, counter())
    assert "FOURCE_SECRET_KEY=secret-0" in filled
    assert "FOURCE_POSTGRES_PASSWORD=secret-1" in filled
    assert "# a comment with change-me in it stays" in filled
    assert "FOURCE_ORG=default" in filled
    assert "${FOURCE_POSTGRES_APP_PASSWORD}" in filled


def test_real_secrets_are_long_and_url_safe() -> None:
    filled = env.fill("FOURCE_SECRET_KEY=change-me\n", env.random_secret)
    value = filled.strip().split("=", 1)[1]
    assert len(value) >= 40 and value.replace("-", "").replace("_", "").isalnum()


def test_an_existing_env_file_is_never_touched(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("FOURCE_SECRET_KEY=change-me\n", encoding="utf-8")
    (tmp_path / ".env").write_text("FOURCE_SECRET_KEY=mine\n", encoding="utf-8")
    assert env.ensure_env(tmp_path) is False
    assert (tmp_path / ".env").read_text(encoding="utf-8") == "FOURCE_SECRET_KEY=mine\n"


def test_a_missing_env_file_is_created(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text("FOURCE_SECRET_KEY=change-me\n", encoding="utf-8")
    assert env.ensure_env(tmp_path) is True
    assert "change-me" not in (tmp_path / ".env").read_text(encoding="utf-8")


def test_the_example_defines_each_variable_before_a_line_refers_to_it() -> None:
    # python-dotenv fills in ${NAME} only from lines above it, so order matters, even in the
    # commented-out lines that a developer will uncomment.
    example = Path(__file__).resolve().parents[2] / ".env.example"
    assigned: set[str] = set()
    for number, line in enumerate(example.read_text(encoding="utf-8").splitlines(), start=1):
        for name in re.findall(r"\$\{([A-Z][A-Z0-9_]*)\}", line):
            assert name in assigned, f"line {number} refers to ${{{name}}} before it is set"
        if match := re.match(r"([A-Z][A-Z0-9_]*)=", line):
            assigned.add(match[1])
