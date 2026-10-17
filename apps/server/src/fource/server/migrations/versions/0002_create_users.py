"""Create the users table, confined to its organisation."""

import sqlalchemy as sa
from alembic import op

from fource.db import UtcDateTime, org_isolation_sql

revision = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("failed_signins", sa.Integer(), nullable=False),
        sa.Column("locked_until", UtcDateTime(), nullable=True),
        sa.UniqueConstraint("org_id", "email"),
    )
    if op.get_bind().dialect.name == "postgresql":
        for statement in org_isolation_sql("users"):
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("users")
