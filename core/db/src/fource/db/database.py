import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

from sqlalchemy import Connection, event, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import ORMExecuteState, Session, SessionTransaction, with_loader_criteria

from fource.common import FourceError
from fource.db.models import Org, OrgScoped


class CrossOrgWrite(FourceError):
    code = "cross_org_write"
    status = 403


class ScopedSession(Session):
    """A session confined to the organisation in info["org_id"]: reads are filtered, new rows
    are stamped, and rows of another organisation can't be written. On PostgreSQL the same
    organisation is also set for row-level security, the backstop if code forgets."""


@event.listens_for(ScopedSession, "do_orm_execute")
def _confine(state: ORMExecuteState) -> None:
    org_id = state.session.info.get("org_id")
    if org_id is None or state.is_column_load:
        return
    if state.is_select or state.is_update or state.is_delete:
        state.statement = state.statement.options(
            with_loader_criteria(OrgScoped, lambda cls: cls.org_id == org_id, include_aliases=True)
        )


@event.listens_for(ScopedSession, "before_flush")
def _stamp(session: Session, flush_context: Any, instances: Any) -> None:
    org_id = session.info.get("org_id")
    if org_id is None:
        return
    for row in [*session.new, *session.dirty]:
        if isinstance(row, OrgScoped):
            # The mapping says UUID, but a new row's org_id is None until something sets it.
            current = cast("uuid.UUID | None", row.org_id)
            if current is None:
                row.org_id = org_id
            elif current != org_id:
                raise CrossOrgWrite("A record can only be written within its own organisation.")


@event.listens_for(ScopedSession, "after_begin")
def _set_org_for_row_security(
    session: Session, transaction: SessionTransaction, connection: Connection
) -> None:
    org_id = session.info.get("org_id")
    if org_id is not None and connection.dialect.name == "postgresql":
        connection.execute(
            text("SELECT set_config('fource.org_id', :org_id, true)"), {"org_id": str(org_id)}
        )


def _enforce_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Database:
    """One database: SQLite (the zero-setup default) or PostgreSQL 18 (production)."""

    def __init__(self, url: str) -> None:
        parsed = make_url(url)
        is_sqlite = parsed.get_backend_name() == "sqlite"
        if is_sqlite and parsed.database not in (None, "", ":memory:"):
            Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_async_engine(parsed)
        if is_sqlite:
            event.listen(self.engine.sync_engine, "connect", _enforce_foreign_keys)
        self._sessions = async_sessionmaker(
            self.engine, sync_session_class=ScopedSession, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """Unscoped: only for tables without an organisation (orgs) and set-up work."""
        async with self._sessions() as session:
            yield session

    @asynccontextmanager
    async def org_session(self, org_id: uuid.UUID) -> AsyncGenerator[AsyncSession]:
        """Everything read or written here belongs to one organisation. Commits on success."""
        async with self._sessions(info={"org_id": org_id}) as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    async def org_id(self, slug: str) -> uuid.UUID | None:
        async with self.session() as session:
            return await session.scalar(select(Org.id).where(Org.slug == slug))

    async def org_slug(self, org_id: uuid.UUID) -> str | None:
        async with self.session() as session:
            return await session.scalar(select(Org.slug).where(Org.id == org_id))

    async def ping(self) -> bool:
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except (SQLAlchemyError, OSError):
            return False
        return True

    async def dispose(self) -> None:
        await self.engine.dispose()
