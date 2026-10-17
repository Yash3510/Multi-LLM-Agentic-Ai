import re

APP_ROLE = "fource_app"
_TABLE = re.compile(r"[a-z_][a-z0-9_]*")
_RULE = "org_id = NULLIF(current_setting('fource.org_id', true), '')::uuid"


def org_isolation_sql(table: str) -> list[str]:
    """PostgreSQL statements that confine a table to the session's organisation.

    FORCE applies the policy to the table's owner too; superusers still bypass it, which is
    why the server connects as APP_ROLE. Migrations run these on PostgreSQL only.
    """
    if not _TABLE.fullmatch(table):
        raise ValueError(f"not a plain table name: {table!r}")
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"CREATE POLICY org_isolation ON {table} USING ({_RULE}) WITH CHECK ({_RULE})",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO {APP_ROLE}",
    ]
