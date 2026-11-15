from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from fource.db import Base, OrgScoped, UtcDateTime


class StoredFile(OrgScoped, Base):
    """The record of one stored file (ADR-0044). Never deleted: deleting a file marks it, and
    erasing its bytes marks it again. The app role has no DELETE on this table."""

    __tablename__ = "stored_files"
    __table_args__ = (CheckConstraint("size >= 0", name="stored_files_size"),)

    name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    created_by: Mapped[str] = mapped_column(String(200))
    deleted_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    deleted_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    erased_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
