"""Create the records of stored files, confined to their organisation (ADR-0043)."""

import sqlalchemy as sa
from alembic import op

from fource.db import UtcDateTime, org_isolation_sql

revision = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "stored_files",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_by", sa.String(200), nullable=False),
        sa.Column("deleted_at", UtcDateTime(), nullable=True),
        sa.Column("deleted_by", sa.String(200), nullable=True),
        sa.Column("erased_at", UtcDateTime(), nullable=True),
        sa.CheckConstraint("size >= 0", name="stored_files_size"),
    )
    if op.get_bind().dialect.name == "postgresql":
        # No DELETE: a record outlives its bytes (ADR-0043).
        for statement in org_isolation_sql("stored_files", ("SELECT", "INSERT", "UPDATE")):
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("stored_files")  # its index goes with it
