"""Create the revoked-token list, confined to its organisation."""

import sqlalchemy as sa
from alembic import op

from fource.db import UtcDateTime, org_isolation_sql

revision = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("token_id", sa.Uuid(), nullable=False, unique=True),
        sa.Column("expires_at", UtcDateTime(), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        for statement in org_isolation_sql("revoked_tokens"):
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("revoked_tokens")
