"""Create the job queue, confined to its organisation (ADR-0040)."""

import sqlalchemy as sa
from alembic import op

from fource.db import UtcDateTime, org_isolation_sql

revision = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None

UNFINISHED = "state IN ('queued', 'running')"


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("orgs.id"), nullable=False, index=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("kind", sa.String(100), nullable=False),
        sa.Column("key", sa.String(200), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("run_at", UtcDateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", UtcDateTime(), nullable=True),
        sa.Column("holder", sa.Uuid(), nullable=True),
        sa.Column("last_error", sa.String(1000), nullable=True),
        sa.Column("finished_at", UtcDateTime(), nullable=True),
        sa.CheckConstraint("state IN ('queued', 'running', 'done', 'failed')", name="jobs_state"),
    )
    op.create_index("jobs_due", "jobs", ["org_id", "state", "run_at"])
    op.create_index(
        "jobs_one_unfinished_per_key",
        "jobs",
        ["org_id", "key"],
        unique=True,
        sqlite_where=sa.text(UNFINISHED),
        postgresql_where=sa.text(UNFINISHED),
    )
    if op.get_bind().dialect.name == "postgresql":
        for statement in org_isolation_sql("jobs"):
            op.execute(statement)


def downgrade() -> None:
    op.drop_table("jobs")  # its indexes go with it
