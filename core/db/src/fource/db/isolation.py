import re

APP_ROLE = "fource_app"
_TABLE = re.compile(r"[a-z_][a-z0-9_]*")
_RULE = "org_id = NULLIF(current_setting('fource.org_id', true), '')::uuid"
_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE")


def org_isolation_sql(table: str, privileges: tuple[str, ...] = _PRIVILEGES) -> list[str]:
    """PostgreSQL statements that confine a table to the session's organisation.

    FORCE applies the policy to the table's owner too; superusers still bypass it, which is
    why the server connects as APP_ROLE. Migrations run these on PostgreSQL only. A table the
    app role must not change (the ledger) grants fewer `privileges`.
    """
    if not _TABLE.fullmatch(table):
        raise ValueError(f"not a plain table name: {table!r}")
    if not privileges or not set(privileges) <= set(_PRIVILEGES):
        raise ValueError(f"privileges are some of {', '.join(_PRIVILEGES)}: {privileges!r}")
    return [
        f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY",
        f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY",
        f"CREATE POLICY org_isolation ON {table} USING ({_RULE}) WITH CHECK ({_RULE})",
        f"GRANT {', '.join(privileges)} ON {table} TO {APP_ROLE}",
    ]
