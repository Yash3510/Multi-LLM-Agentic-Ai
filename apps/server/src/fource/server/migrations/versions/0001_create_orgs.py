"""Create the organisations table and the default organisation."""

import sqlalchemy as sa
from alembic import op

from fource.common import new_id, now
from fource.db import APP_ROLE, UtcDateTime

revision = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    orgs = op.create_table(
        "orgs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
    )
    op.bulk_insert(
        orgs,
        [{"id": new_id(), "slug": "default", "name": "Default organisation", "created_at": now()}],
    )
    if op.get_bind().dialect.name == "postgresql":
        # The app role reads organisations but never writes them.
        op.execute(f"GRANT SELECT ON orgs TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table("orgs")
