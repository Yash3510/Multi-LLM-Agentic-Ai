import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from fource.db import Base, OrgScoped, UtcDateTime

EMAIL_LENGTH = 320
DISPLAY_NAME_LENGTH = 200


class User(OrgScoped, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("org_id", "email"),)

    email: Mapped[str] = mapped_column(String(EMAIL_LENGTH))
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_LENGTH), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_signins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class RevokedToken(OrgScoped, Base):
    """A signed-out token, kept until it would have expired anyway."""

    __tablename__ = "revoked_tokens"

    token_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
