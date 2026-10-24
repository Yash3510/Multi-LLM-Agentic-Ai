import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from fource.db import Base, OrgScoped, UtcDateTime


class LedgerEntry(OrgScoped, Base):
    """One entry of an organisation's chain. Insert-only: a trigger refuses UPDATE and DELETE
    (and TRUNCATE on PostgreSQL), and the app role may only INSERT and SELECT."""

    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("org_id", "seq"),)

    seq: Mapped[int] = mapped_column(BigInteger)
    at: Mapped[datetime] = mapped_column(UtcDateTime)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    type: Mapped[str] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(200))
    inputs_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outputs_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    refs: Mapped[dict[str, str]] = mapped_column(JSON)
    prev: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))


class LedgerHead(OrgScoped, Base):
    """The last seq and hash of an organisation's chain. Writers lock this row to take the
    next seq, so entries never share or skip a number. Not evidence: the verifier never
    reads it."""

    __tablename__ = "ledger_heads"
    __table_args__ = (UniqueConstraint("org_id"),)

    seq: Mapped[int] = mapped_column(BigInteger)
    hash: Mapped[str] = mapped_column(String(64))
