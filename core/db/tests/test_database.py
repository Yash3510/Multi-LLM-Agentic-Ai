import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import String, delete, select
from sqlalchemy.orm import Mapped, mapped_column

from fource.db import Base, CrossOrgWrite, Database, Org, OrgScoped

pytestmark = pytest.mark.anyio


class Note(OrgScoped, Base):
    """A test-only table that is scoped to an organisation."""

    __tablename__ = "scoping_notes"
    text: Mapped[str] = mapped_column(String(50))


async def two_orgs(database: Database) -> tuple[uuid.UUID, uuid.UUID]:
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    first, second = Org(slug="first", name="First"), Org(slug="second", name="Second")
    async with database.session() as session:
        session.add_all([first, second])
        await session.commit()
    for org, text in ((first.id, "for-first"), (second.id, "for-second")):
        async with database.org_session(org) as session:
            session.add(Note(text=text))
    return first.id, second.id


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[Database]:
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    yield database
    await database.dispose()


async def test_a_session_reads_only_its_own_organisation(database: Database) -> None:
    first, _ = await two_orgs(database)
    async with database.org_session(first) as session:
        assert (await session.scalars(select(Note.text))).all() == ["for-first"]


async def test_new_rows_take_the_session_organisation(database: Database) -> None:
    first, _ = await two_orgs(database)
    async with database.org_session(first) as session:
        note = Note(text="later")
        session.add(note)
        await session.flush()
        assert note.org_id == first


async def test_writing_into_another_organisation_is_refused(database: Database) -> None:
    first, second = await two_orgs(database)
    with pytest.raises(CrossOrgWrite):
        async with database.org_session(first) as session:
            session.add(Note(text="sneaky", org_id=second))
    async with database.org_session(second) as session:
        assert (await session.scalars(select(Note.text))).all() == ["for-second"]


async def test_deleting_another_organisations_row_is_refused(database: Database) -> None:
    first, second = await two_orgs(database)
    async with database.session() as session:
        theirs = (await session.scalars(select(Note).where(Note.org_id == second))).one()
    with pytest.raises(CrossOrgWrite):
        async with database.org_session(first) as session:
            await session.delete(theirs)
    async with database.session() as session:
        remaining = await session.scalars(select(Note.text).where(Note.org_id == second))
        assert remaining.all() == ["for-second"]


async def test_reassigning_another_organisations_row_is_refused(database: Database) -> None:
    first, second = await two_orgs(database)
    async with database.session() as session:
        theirs = (await session.scalars(select(Note).where(Note.org_id == second))).one()
    theirs.org_id = first
    with pytest.raises(CrossOrgWrite):
        async with database.org_session(first) as session:
            session.add(theirs)
    async with database.session() as session:
        owners = await session.scalars(select(Note.org_id).where(Note.text == "for-second"))
        assert owners.all() == [second]


async def test_reassigning_then_deleting_another_organisations_row_is_refused(
    database: Database,
) -> None:
    first, second = await two_orgs(database)
    async with database.session() as session:
        theirs = (await session.scalars(select(Note).where(Note.org_id == second))).one()
    theirs.org_id = first
    with pytest.raises(CrossOrgWrite):
        async with database.org_session(first) as session:
            await session.delete(theirs)
    async with database.session() as session:
        owners = await session.scalars(select(Note.org_id).where(Note.text == "for-second"))
        assert owners.all() == [second]


async def test_reassigning_an_expired_row_is_refused(
    database: Database,
) -> None:
    first, second = await two_orgs(database)
    async with database.session() as session:
        theirs = (await session.scalars(select(Note).where(Note.org_id == second))).one()
        session.expire(theirs)
        theirs.org_id = first
        session.expunge(theirs)
    with pytest.raises(CrossOrgWrite):
        async with database.org_session(first) as session:
            session.add(theirs)
    async with database.session() as session:
        owners = await session.scalars(select(Note.org_id).where(Note.text == "for-second"))
        assert owners.all() == [second]


async def test_bulk_deletes_stay_inside_the_organisation(database: Database) -> None:
    first, second = await two_orgs(database)
    async with database.org_session(first) as session:
        await session.execute(delete(Note))
    async with database.org_session(first) as session:
        assert (await session.scalars(select(Note.text))).all() == []
    async with database.org_session(second) as session:
        assert (await session.scalars(select(Note.text))).all() == ["for-second"]


async def test_an_error_rolls_the_session_back(database: Database) -> None:
    first, _ = await two_orgs(database)
    with pytest.raises(RuntimeError):
        async with database.org_session(first) as session:
            session.add(Note(text="lost"))
            await session.flush()
            raise RuntimeError("boom")
    async with database.org_session(first) as session:
        assert (await session.scalars(select(Note.text))).all() == ["for-first"]


async def test_organisations_are_found_by_slug(database: Database) -> None:
    first, _ = await two_orgs(database)
    assert await database.org_id("first") == first
    assert await database.org_slug(first) == "first"
    assert await database.org_id("missing") is None


async def test_a_fresh_clone_gets_its_data_folder(tmp_path: Path) -> None:
    nested = tmp_path / "not" / "there" / "yet.db"
    database = Database(f"sqlite+aiosqlite:///{nested.as_posix()}")
    try:
        assert await database.ping()
        assert nested.parent.is_dir()
    finally:
        await database.dispose()


async def test_ping_reports_an_unreachable_database() -> None:
    database = Database("postgresql+psycopg://nobody:wrong@127.0.0.1:1/none")
    try:
        assert await database.ping() is False
    finally:
        await database.dispose()
