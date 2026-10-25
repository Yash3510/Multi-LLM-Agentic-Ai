import pytest

from fource.server.main import UnsafeDatabaseRole, refuse_a_bypassing_role


@pytest.mark.parametrize("role", ["fource", "postgres"])
def test_a_role_that_bypasses_row_level_security_is_refused(role: str) -> None:
    with pytest.raises(UnsafeDatabaseRole) as refused:
        refuse_a_bypassing_role(role, bypasses=True)
    message = refused.value.message
    assert f"'{role}'" in message
    assert "fource_app" in message and "FOURCE_DATABASE_URL" in message
    # Whichever of the three it is, the message says so: the owner of the tables can switch
    # off the ledger's trigger and its row-level security.
    assert "superuser" in message and "row-level security" in message
    assert "owns the 4CE tables" in message
    assert "://" not in message  # no URL, so no password either


def test_a_role_that_does_not_bypass_row_level_security_is_accepted() -> None:
    refuse_a_bypassing_role("fource_app", bypasses=False)
