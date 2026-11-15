"""Make SQLite refuse deleting a file record, as PostgreSQL does (ADR-0044).

A record outlives its bytes: deleting a file marks it (`deleted_at`) and a job erases the bytes
(`erased_at`), but the row stays. On PostgreSQL the app role has no DELETE grant. SQLite has no
roles, so a trigger refuses instead, and a stray `DELETE` fails in tests, not only in production.
"""

from alembic import op

revision = "0007"
down_revision: str | None = "0006"
branch_labels: str | None = None
depends_on: str | None = None

NEVER_DELETED = "stored_files rows are never deleted"
SQLITE_TRIGGER = (
    "CREATE TRIGGER stored_files_no_delete BEFORE DELETE ON stored_files"
    f" BEGIN SELECT RAISE(ABORT, '{NEVER_DELETED}'); END"
)


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute(SQLITE_TRIGGER)


def downgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("DROP TRIGGER stored_files_no_delete")
