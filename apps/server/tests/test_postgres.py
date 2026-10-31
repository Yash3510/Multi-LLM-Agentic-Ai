import asyncio
import secrets
import uuid
from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from datetime import timedelta

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import Settings, new_id, now
from fource.db import Database
from fource.identity import InvalidEmail, Role, create_user
from fource.jobs import Handler, HeldJob, Worker, enqueue, listen_for_jobs, take
from fource.ledger import EntryType, append, read_entries, verify_ledger
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


async def test_the_server_refuses_to_start_as_a_non_superuser_role_with_bypassrls(
    postgres: tuple[str, str],
) -> None:
    # The owner above is a superuser; this role is not, so only BYPASSRLS can make it unsafe.
    # Roles belong to the cluster, so dropping the test database would not remove it. (Any role
    # may connect to a new database, so it needs no grant.)
    owner = make_url(postgres[0])
    role = f"fource_test_bypass_{uuid.uuid4().hex[:12]}"
    password = secrets.token_hex(16)
    admin = create_engine(owner, isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(
                f"CREATE ROLE {role} LOGIN NOSUPERUSER BYPASSRLS PASSWORD '{password}'"
            )
        url = owner.set(username=role, password=password).render_as_string(hide_password=False)
        app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(url)))
        with pytest.raises(UnsafeDatabaseRole) as refused:
            async with app.router.lifespan_context(app):
                pass
    finally:
        with admin.connect() as connection:
            connection.exec_driver_sql(f"DROP ROLE IF EXISTS {role}")
        admin.dispose()
    message = refused.value.message
    assert f"'{role}'" in message and "fource_app" in message
    assert password not in message


async def test_the_server_refuses_to_start_as_the_owner_of_the_ledger_tables(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    # On managed PostgreSQL the owner is often not a superuser. As owner it could still switch
    # the ledger's trigger off or remove its forced row-level security, so it is refused too.
    # Roles belong to the cluster, so the role is dropped in the end, and the table goes back to
    # its owner first (a role that owns something can't be dropped).
    owner = make_url(postgres[0])
    assert owner.username is not None
    role = f"fource_test_owner_{uuid.uuid4().hex[:12]}"
    password = secrets.token_hex(16)
    admin = create_engine(owner, isolation_level="AUTOCOMMIT")
    created = handed_over = False
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(
                f"CREATE ROLE {role} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"
            )
            created = True
            connection.exec_driver_sql(f"GRANT CREATE ON SCHEMA public TO {role}")
            connection.exec_driver_sql(f"ALTER TABLE ledger_entries OWNER TO {role}")
            handed_over = True
        url = owner.set(username=role, password=password).render_as_string(hide_password=False)
        app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(url)))
        with pytest.raises(UnsafeDatabaseRole) as refused:
            async with app.router.lifespan_context(app):
                pass
    finally:
        with admin.connect() as connection:
            if handed_over:
                connection.exec_driver_sql(
                    f'ALTER TABLE ledger_entries OWNER TO "{owner.username}"'
                )
            if created:
                connection.exec_driver_sql(f"REVOKE CREATE ON SCHEMA public FROM {role}")
                connection.exec_driver_sql(f"DROP ROLE {role}")
        admin.dispose()
    message = refused.value.message
    assert f"'{role}'" in message and "owns tables under row-level security" in message
    assert password not in message


async def test_the_server_refuses_to_start_as_a_noinherit_member_of_the_owner(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    # NOINHERIT: the role holds none of the owner's privileges until it runs SET ROLE, which it
    # may do at any time, so pg_has_role(..., 'USAGE') says no while 'MEMBER' says yes. Roles
    # belong to the cluster, so the role is dropped in the end (its membership goes with it).
    owner = make_url(postgres[0])
    assert owner.username is not None
    role = f"fource_test_member_{uuid.uuid4().hex[:12]}"
    password = secrets.token_hex(16)
    admin = create_engine(owner, isolation_level="AUTOCOMMIT")
    created = False
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(
                f"CREATE ROLE {role} LOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"
            )
            created = True
            connection.exec_driver_sql(f'GRANT "{owner.username}" TO {role}')
        url = owner.set(username=role, password=password).render_as_string(hide_password=False)
        app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(url)))
        with pytest.raises(UnsafeDatabaseRole) as refused:
            async with app.router.lifespan_context(app):
                pass
    finally:
        with admin.connect() as connection:
            if created:
                connection.exec_driver_sql(f"DROP ROLE {role}")
        admin.dispose()
    message = refused.value.message
    assert f"'{role}'" in message and "member of a role that does" in message
    assert password not in message


async def test_the_server_refuses_to_start_as_the_owner_of_any_table_under_row_level_security(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    # Not only the ledger's owner: whoever owns users could remove that table's forced
    # row-level security. The table goes back to its owner before the role is dropped.
    owner = make_url(postgres[0])
    assert owner.username is not None
    role = f"fource_test_owner_{uuid.uuid4().hex[:12]}"
    password = secrets.token_hex(16)
    admin = create_engine(owner, isolation_level="AUTOCOMMIT")
    created = handed_over = False
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(
                f"CREATE ROLE {role} LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '{password}'"
            )
            created = True
            connection.exec_driver_sql(f"GRANT CREATE ON SCHEMA public TO {role}")
            connection.exec_driver_sql(f"ALTER TABLE users OWNER TO {role}")
            handed_over = True
        url = owner.set(username=role, password=password).render_as_string(hide_password=False)
        app = create_app(Settings(secret_key=SecretStr(SECRET), database_url=SecretStr(url)))
        with pytest.raises(UnsafeDatabaseRole) as refused:
            async with app.router.lifespan_context(app):
                pass
    finally:
        with admin.connect() as connection:
            if handed_over:
                connection.exec_driver_sql(f'ALTER TABLE users OWNER TO "{owner.username}"')
            if created:
                connection.exec_driver_sql(f"REVOKE CREATE ON SCHEMA public FROM {role}")
                connection.exec_driver_sql(f"DROP ROLE {role}")
        admin.dispose()
    message = refused.value.message
    assert f"'{role}'" in message and "owns tables under row-level security" in message
    assert password not in message


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
        # The INSERT grant: one entry for its own organisation (a checkpoint-shaped row; the
        # chain's validity is not what is tested here).
        connection.execute(
            text(
                "INSERT INTO ledger_entries (id, org_id, created_at, seq, at, type, actor,"
                " refs, prev, hash) VALUES (:id, :org, now(), 99, now(), 'checkpoint',"
                " 'system', '{}', :zero, :zero)"
            ),
            {"id": new_id(), "org": users[0], "zero": "0" * 64},
        )
        assert connection.execute(text("SELECT count(*) FROM ledger_entries")).scalar() == 2


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


async def test_concurrent_first_writers_of_an_empty_ledger_take_one_to_twenty(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """The head row doesn't exist yet: every writer races to create it, then to bump it."""
    database = Database(postgres[1])

    async def write() -> None:
        async with database.org_session(orgs[1]) as session:
            await append(session, EntryType.SIGNOUT, actor="system")

    try:
        await asyncio.gather(*(write() for _ in range(20)))
        async with database.org_session(orgs[1]) as session:
            seqs = [entry.seq async for entry in read_entries(session)]
            result = await verify_ledger(session)
    finally:
        await database.dispose()
    assert seqs == list(range(1, 21))
    assert result.ok and (result.entries, result.head_seq) == (20, 20)


async def test_a_deeply_nested_refs_cell_fails_verification_cleanly_on_postgres(
    postgres: tuple[str, str], users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """On CPython 3.12 the driver decodes this 2000-deep value, so verification reports the
    entry as "altered" (its refs are not an object). The "unreadable" path, where the driver
    raises RecursionError while fetching (fource.ledger.store.read_entries), is not reached
    here: the stubbed tests in core/ledger/tests/test_store.py cover it. Either kind passes, so
    an interpreter that fails to decode the value is accepted too."""
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


async def test_each_organisation_sees_only_its_own_jobs_on_postgres(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    database = Database(postgres[1])
    try:
        for org_id in orgs:
            async with database.org_session(org_id) as session:
                await enqueue(session, "test.work", {"for": str(org_id)})
    finally:
        await database.dispose()
    with connect(postgres[1]) as connection:
        set_org(connection, orgs[1])
        owners = connection.execute(text("SELECT org_id FROM jobs")).scalars().all()
    assert owners == [orgs[1]]


async def test_a_key_keeps_one_unfinished_job_on_postgres(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    database = Database(postgres[1])
    try:
        ids: list[uuid.UUID] = []
        for _ in range(2):
            async with database.org_session(orgs[0]) as session:
                ids.append(await enqueue(session, "test.work", key="document:d-1"))
    finally:
        await database.dispose()
    assert ids[0] == ids[1]


async def test_takers_take_each_job_once_with_skip_locked(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    database = Database(postgres[1])

    async def taker() -> list[uuid.UUID]:
        taken: list[uuid.UUID] = []
        while True:
            async with database.org_session(orgs[0]) as session:
                job = await take(session, ["test.work"], lease=timedelta(minutes=5))
            if job is None:
                return taken
            taken.append(job.id)

    try:
        expected: set[uuid.UUID] = set()
        for _ in range(20):
            async with database.org_session(orgs[0]) as session:
                expected.add(await enqueue(session, "test.work"))
        results = await asyncio.gather(*(taker() for _ in range(5)))
    finally:
        await database.dispose()
    every = [job_id for taken in results for job_id in taken]
    assert len(every) == 20 and set(every) == expected


async def test_a_worker_runs_each_organisations_jobs_on_postgres(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    ran: list[uuid.UUID] = []

    async def note(session: AsyncSession, job: HeldJob) -> None:
        ran.append(job.org_id)

    database = Database(postgres[1])
    try:
        for org_id in orgs:
            async with database.org_session(org_id) as session:
                await enqueue(session, "test.work")
        assert await Worker(database, {"test.work": Handler(note)}).run_once() == 2
    finally:
        await database.dispose()
    assert sorted(ran) == sorted(orgs)


async def test_a_queued_job_wakes_a_listening_worker(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    woken, stop = asyncio.Event(), asyncio.Event()
    listener = asyncio.create_task(listen_for_jobs(postgres[1], woken.set, stop))
    database = Database(postgres[1])
    try:
        await asyncio.wait_for(woken.wait(), 10)  # it wakes once when it starts listening
        woken.clear()
        async with database.org_session(orgs[0]) as session:
            await enqueue(session, "test.work")
        await asyncio.wait_for(woken.wait(), 10)  # the NOTIFY sent at the commit
    finally:
        stop.set()
        await asyncio.wait_for(listener, 10)
        await database.dispose()


def test_the_jobs_table_is_under_forced_row_level_security(postgres: tuple[str, str]) -> None:
    owner, _ = postgres
    upgrade(owner)
    downgrade(owner, "0004")
    upgrade(owner)
    with connect(owner) as connection:
        flags = connection.execute(
            text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'jobs'")
        ).one()
    assert tuple(flags) == (True, True)
