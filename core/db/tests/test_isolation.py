import pytest

from fource.db import APP_ROLE, org_isolation_sql


def test_isolation_enables_forces_and_grants() -> None:
    statements = org_isolation_sql("users")
    assert statements[0] == "ALTER TABLE users ENABLE ROW LEVEL SECURITY"
    assert statements[1] == "ALTER TABLE users FORCE ROW LEVEL SECURITY"
    assert "CREATE POLICY org_isolation ON users" in statements[2]
    assert statements[3] == f"GRANT SELECT, INSERT, UPDATE, DELETE ON users TO {APP_ROLE}"


def test_the_policy_reads_the_session_organisation_safely() -> None:
    policy = org_isolation_sql("users")[2]
    # An unset setting reads as '' after a transaction; NULLIF keeps that from being cast.
    rule = "org_id = NULLIF(current_setting('fource.org_id', true), '')::uuid"
    assert f"USING ({rule})" in policy and f"WITH CHECK ({rule})" in policy


@pytest.mark.parametrize("name", ["users; DROP TABLE orgs", "Users", "1users", ""])
def test_only_plain_table_names_are_accepted(name: str) -> None:
    with pytest.raises(ValueError):
        org_isolation_sql(name)


def test_a_table_can_grant_the_app_role_fewer_privileges() -> None:
    statements = org_isolation_sql("ledger_entries", privileges=("SELECT", "INSERT"))
    assert statements[3] == f"GRANT SELECT, INSERT ON ledger_entries TO {APP_ROLE}"


@pytest.mark.parametrize("privileges", [(), ("SELECT", "TRUNCATE"), ("select",)])
def test_only_data_privileges_can_be_granted(privileges: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        org_isolation_sql("ledger_entries", privileges=privileges)
