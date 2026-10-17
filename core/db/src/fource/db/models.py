import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fource.common import new_id, now
from fource.db.types import UtcDateTime


class Base(DeclarativeBase):
    """Every 4CE table's base. Alembic in apps/server reads its metadata."""


class Org(Base):
    """An organisation: the root of scoping, so it has no org_id itself."""

    __tablename__ = "orgs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=now)


class OrgScoped:
    """Mixed into every table that belongs to one organisation (master plan §7.24)."""

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_id)
    org_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("orgs.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, default=now)
