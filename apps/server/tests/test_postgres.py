import asyncio
import uuid
from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from fource.common import Settings, new_id, now
from fource.db import Database
from fource.identity import InvalidEmail, Role, create_user
from fource.ledger import EntryType, append, verify_ledger
from fource.server.main import UnsafeDatabaseRole, create_app
from fource.server.migrate import downgrade, upgrade

pytestmark = [pytest.mark.postgres, pytest.mark.anyio]
SECRET = "s" * 40
PASSWORD = "correct horse battery"


@contextmanager
def connect(url: str) -> Generator[Connection]:
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            yield connection
    finally:
        engine.dispose()


def set_org(connection: Connection, org_id: uuid.UUID) -> None:
    connection.execute(
        text("SELECT set_config('fource.org_id', :org, false)"), {"org": str(org_id)}
    )


@pytest.fixture
def orgs(postgres: tuple[str, str]) -> tuple[uuid.UUID, uuid.UUID]:
    """The migrated database with a second organisation. Sync on purpose: migrations run
    their own event loop."""
    owner, _ = postgres
    upgrade(owner)
    second = new_id()
    with connect(owner) as connection:
        first = connection.execute(text("SELECT id FROM orgs WHERE slug = 'default'")).scalar_one()
        connection.execute(
            text(
                "INSERT INTO orgs (id, slug, name, created_at)"
                " VALUES (:id, 'second', 'Second', :at)"
            ),
            {"id": second, "at": now().replace(tzinfo=None)},
        )
        connection.commit()
    return first, second


@pytest.fixture
async def users(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> tuple[uuid.UUID, uuid.UUID]:
    """One user in each organisation, created through the app role."""
    _, app = postgres
    database = Database(app)
    for org_id, email in zip(orgs, ("first@example.com", "second@example.com"), strict=True):
        async with database.org_session(org_id) as session:
            await create_user(session, email=email, password=PASSWORD, roles=[Role.VIEWER])
    await database.dispose()
    return orgs


def test_migrations_go_up_down_and_up_again_on_postgres(postgres: tuple[str, str]) -> None:
    owner, _ = postgres
    upgrade(owner)
    downgrade(owner, "base")
    upgrade(owner)
    with connect(owner) as connection:
        assert connection.execute(text("SELECT to_regclass('public.users')")).scalar() is not None


async def test_the_app_role_sees_nothing_without_an_organisation(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        assert connection.execute(text("SELECT count(*) FROM users")).scalar() == 0


async def test_raw_sql_sees_only_the_set_organisation(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        set_org(connection, users[0])
        emails = connection.execute(text("SELECT email FROM users")).scalars().all()
    assert emails == ["first@example.com"]


async def test_the_app_role_cannot_write_into_another_organisation(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        set_org(connection, users[0])
        with pytest.raises(DBAPIError, match="row-level security"):
            connection.execute(
                text("UPDATE users SET org_id = :other WHERE email = 'first@example.com'"),
                {"other": users[1]},
            )


async def test_the_app_role_cannot_turn_row_level_security_off(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        with pytest.raises(DBAPIError, match="owner"):
            connection.execute(text("ALTER TABLE users DISABLE ROW LEVEL SECURITY"))


@pytest.fixture
async def pg_client(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(postgres[1]))
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    await app.state.database.dispose()


async def test_sign_in_end_to_end_on_postgres(pg_client: httpx.AsyncClient) -> None:
    signed_in = await pg_client.post(
        "/api/auth/signin", json={"email": "first@example.com", "password": PASSWORD}
    )
    assert signed_in.status_code == 200
    assert (await pg_client.get("/api/auth/session")).json()["email"] == "first@example.com"


async def test_five_wrong_passwords_lock_the_account_on_postgres(
    pg_client: httpx.AsyncClient,
) -> None:
    for _ in range(5):
        wrong = await pg_client.post(
            "/api/auth/signin", json={"email": "first@example.com", "password": "wrong password!"}
        )
        assert wrong.status_code == 401
    locked = await pg_client.post(
        "/api/auth/signin", json={"email": "first@example.com", "password": PASSWORD}
    )
    assert (locked.status_code, locked.json()["error"]["code"]) == (423, "account_locked")


@pytest.mark.parametrize(
    "email", ["a\x00@example.com", "e" * 320 + "@example.com"], ids=["nul", "too-long"]
)
async def test_unstorable_emails_raise_the_domain_error_on_postgres(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID], email: str
) -> None:
    database = Database(postgres[1])
    try:
        async with database.org_session(orgs[0]) as session:
            with pytest.raises(InvalidEmail):
                await create_user(session, email=email, password=PASSWORD, roles=[])
    finally:
        await database.dispose()


async def test_the_server_refuses_to_start_as_a_role_that_bypasses_row_level_security(
    postgres: tuple[str, str],
) -> None:
    owner = postgres[0]
    app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(owner)))
    with pytest.raises(UnsafeDatabaseRole) as refused:
        async with app.router.lifespan_context(app):
            pass
    url = make_url(owner)
    message = refused.value.message
    assert f"'{url.username}'" in message and "fource_app" in message
    assert url.password is not None and url.password not in message


async def test_the_server_starts_and_stops_as_the_app_role(postgres: tuple[str, str]) -> None:
    app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(postgres[1])))
    async with app.router.lifespan_context(app):
        assert await app.state.database.ping()


LEDGER_CHANGES = (
    "UPDATE ledger_entries SET actor = 'anonymous'",
    "DELETE FROM ledger_entries",
    "TRUNCATE ledger_entries",
)


async def test_the_app_role_may_only_add_and_read_ledger_entries(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        for statement in LEDGER_CHANGES:
            set_org(connection, users[0])  # again: the rollback below undoes it
            with pytest.raises(DBAPIError, match="permission denied"):
                connection.execute(text(statement))
            connection.rollback()
        set_org(connection, users[0])
        assert connection.execute(text("SELECT count(*) FROM ledger_entries")).scalar() == 1


async def test_the_app_role_cannot_delete_a_ledger_head(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        set_org(connection, users[0])
        with pytest.raises(DBAPIError, match="permission denied"):
            connection.execute(text("DELETE FROM ledger_heads"))


async def test_even_the_owner_cannot_change_or_empty_the_ledger(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    # The owner is the bundled image's superuser, so row-level security does not apply to it;
    # the trigger refuses it regardless. (Setting the organisation keeps the test true for an
    # owner that is not a superuser, whose forced policy would otherwise hide every row.)
    with connect(postgres[0]) as connection:
        for statement in LEDGER_CHANGES:
            set_org(connection, users[0])  # again: the rollback below undoes it
            with pytest.raises(DBAPIError, match="insert-only"):
                connection.execute(text(statement))
            connection.rollback()


@pytest.mark.parametrize("table", ["ledger_entries", "ledger_heads"])
async def test_row_level_security_is_enabled_and_forced_on_the_ledger(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID], table: str
) -> None:
    with connect(postgres[0]) as connection:
        flags = connection.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = :t"),
            {"t": table},
        ).one()
    assert tuple(flags) == (True, True)


async def test_each_organisation_reads_only_its_own_ledger_on_postgres(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        set_org(connection, users[1])
        owners = connection.execute(text("SELECT org_id FROM ledger_entries")).scalars().all()
        heads = connection.execute(text("SELECT org_id FROM ledger_heads")).scalars().all()
    assert owners == [users[1]]
    assert heads == [users[1]]


async def test_the_app_role_cannot_add_an_entry_to_another_organisations_ledger(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    with connect(postgres[1]) as connection:
        set_org(connection, users[0])
        with pytest.raises(DBAPIError, match="row-level security"):
            connection.execute(
                text(
                    "INSERT INTO ledger_entries (id, org_id, created_at, seq, at, type, actor,"
                    " refs, prev, hash) VALUES (:id, :org, now(), 99, now(), 'checkpoint',"
                    " 'system', '{}', :zero, :zero)"
                ),
                {"id": new_id(), "org": users[1], "zero": "0" * 64},
            )


async def test_concurrent_writers_keep_the_chain_whole_on_postgres(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    database = Database(postgres[1])

    async def write() -> None:
        async with database.org_session(users[0]) as session:
            await append(session, EntryType.SIGNOUT, actor="system")

    try:
        await asyncio.gather(*(write() for _ in range(20)))
        async with database.org_session(users[0]) as session:
            result = await verify_ledger(session)
    finally:
        await database.dispose()
    assert result.ok and (result.entries, result.head_seq) == (21, 21)


async def test_a_deeply_nested_refs_cell_fails_verification_cleanly_on_postgres(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    deep = "[" * 2000 + "]" * 2000
    with connect(postgres[0]) as connection:
        # Only the owner may switch the trigger off, which is how a tampered cell gets in.
        set_org(connection, users[0])
        connection.execute(
            text("ALTER TABLE ledger_entries DISABLE TRIGGER ledger_entries_insert_only")
        )
        connection.execute(
            text("UPDATE ledger_entries SET refs = CAST(:deep AS json) WHERE org_id = :org"),
            {"deep": deep, "org": users[0]},
        )
        connection.execute(
            text("ALTER TABLE ledger_entries ENABLE TRIGGER ledger_entries_insert_only")
        )
        connection.commit()
        stored = connection.execute(
            text("SELECT length(CAST(refs AS text)) FROM ledger_entries WHERE org_id = :org"),
            {"org": users[0]},
        ).scalar_one()
    assert stored == len(deep)  # the deep value really is in the database
    database = Database(postgres[1])
    try:
        async with database.org_session(users[0]) as session:
            result = await verify_ledger(session)
    finally:
        await database.dispose()
    assert not result.ok
    assert {problem.kind for problem in result.problems} & {"altered", "unreadable"}
