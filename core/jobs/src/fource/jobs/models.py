import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, CheckConstraint, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from fource.db import Base, OrgScoped, UtcDateTime


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


UNFINISHED = (JobState.QUEUED.value, JobState.RUNNING.value)
# The partial index's condition, as text: SQLite matches an ON CONFLICT target to a partial
# index only when the two conditions are written alike, never with bound values.
UNFINISHED_SQL = "state IN ('queued', 'running')"


class Job(OrgScoped, Base):
    """One unit of work for a worker, belonging to one organisation (ADR-0040)."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("state IN ('queued', 'running', 'done', 'failed')", name="jobs_state"),
        Index("jobs_due", "org_id", "state", "run_at"),
        Index(
            "jobs_one_unfinished_per_key",
            "org_id",
            "key",
            unique=True,
            sqlite_where=text(UNFINISHED_SQL),
            postgresql_where=text(UNFINISHED_SQL),
        ),
    )

    kind: Mapped[str] = mapped_column(String(100))
    key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON)
    state: Mapped[str] = mapped_column(String(16))
    run_at: Mapped[datetime] = mapped_column(UtcDateTime)
    attempts: Mapped[int] = mapped_column(Integer)
    max_attempts: Mapped[int] = mapped_column(Integer)
    locked_until: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    holder: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)  # fresh per take
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
