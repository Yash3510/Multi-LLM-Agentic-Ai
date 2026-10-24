"""Create the ledger: insert-only entries and the head row writers lock, per organisation."""

import sqlalchemy as sa
from alembic import op

from fource.db import UtcDateTime, org_isolation_sql

revision = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None

INSERT_ONLY = "ledger_entries is insert-only"
POSTGRES_FUNCTION = f"""
CREATE FUNCTION ledger_insert_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION '{INSERT_ONLY}';
END
$$
"""
POSTGRES_TRIGGERS = [
    "CREATE TRIGGER ledger_entries_insert_only BEFORE UPDATE OR DELETE ON ledger_entries"
    " FOR EACH ROW EXECUTE FUNCTION ledger_insert_only()",
    "CREATE TRIGGER ledger_entries_no_truncate BEFORE TRUNCATE ON ledger_entries"
    " FOR EACH STATEMENT EXECUTE FUNCTION ledger_insert_only()",
]
SQLITE_TRIGGERS = [
    f"CREATE TRIGGER ledger_entries_no_{action.lower()} BEFORE {action} ON ledger_entries"
    f" BEGIN SELECT RAISE(ABORT, '{INSERT_ONLY}'); END"
    for action in ("UPDATE", "DELETE")
]


def upgrade() -> None:
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("at", UtcDateTime(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.String(64), nullable=False),
        sa.Column("actor", sa.String(200), nullable=False),
        sa.Column("inputs_sha256", sa.String(64), nullable=True),
        sa.Column("outputs_sha256", sa.String(64), nullable=True),
        sa.Column("refs", sa.JSON(), nullable=False),
        sa.Column("prev", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("org_id", "seq"),
    )
    op.create_table(
        "ledger_heads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("org_id"),
    )
    if op.get_bind().dialect.name == "postgresql":
        # The app role may add entries and read them, never change them.
        entries = org_isolation_sql("ledger_entries", privileges=("SELECT", "INSERT"))
        heads = org_isolation_sql("ledger_heads", privileges=("SELECT", "INSERT", "UPDATE"))
        for statement in [*entries, *heads]:
            op.execute(statement)
        op.execute(POSTGRES_FUNCTION)
        for statement in POSTGRES_TRIGGERS:
            op.execute(statement)
    else:
        for statement in SQLITE_TRIGGERS:
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("ledger_heads")
    op.drop_table("ledger_entries")  # its triggers go with it
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP FUNCTION ledger_insert_only()")
