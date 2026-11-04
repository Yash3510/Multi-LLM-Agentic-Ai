import pytest

from fource.server.main import UnsafeDatabaseRole, refuse_a_bypassing_role


@pytest.mark.parametrize("role", ["fource", "postgres"])
def test_a_role_that_bypasses_row_level_security_is_refused(role: str) -> None:
    with pytest.raises(UnsafeDatabaseRole) as refused:
        refuse_a_bypassing_role(role, bypasses=True)
    message = refused.value.message
    assert f"'{role}'" in message
    # The worker refuses with the same text, so it names neither command.
    assert "Connect 4CE as fource_app through FOURCE_DATABASE_URL." in message
    assert "server" not in message.lower()
    # Whichever it is, the message says so: the owner of a table under row-level security, or
    # a member of its role, can switch the table's policy (and the ledger's trigger) off.
    assert "superuser" in message and "bypasses row-level security" in message
    assert "owns tables under row-level security" in message
    assert "member of a role that does" in message
    assert "://" not in message  # no URL, so no password either


def test_a_role_that_does_not_bypass_row_level_security_is_accepted() -> None:
    refuse_a_bypassing_role("fource_app", bypasses=False)
