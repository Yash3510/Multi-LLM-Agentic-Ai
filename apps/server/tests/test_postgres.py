import asyncio
import logging
import os
import secrets
import uuid
from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

import httpx
import psycopg
import pytest
from pydantic import SecretStr
from sqlalchemy import Connection, create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import Settings, new_id, now
from fource.db import Database
from fource.identity import InvalidEmail, Role, create_user
from fource.jobs import (
    Handler,
    HeldJob,
    Job,
    Recurring,
    Worker,
    enqueue,
    listen_for_jobs,
    take,
)
from fource.ledger import EntryType, append, read_entries, verify_ledger
from fource.server import cli
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


def conninfo(url: str) -> str:
    return make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)


async def listener_pid(owner: str) -> int:
    """The backend of a job listener that is connected and idle, as the owner sees it. One async
    connection, so waiting never blocks the event loop the worker and listener run on."""
    database = make_url(owner).database

    async def look() -> int:
        async with await psycopg.AsyncConnection.connect(conninfo(owner), autocommit=True) as seen:
            while True:
                cursor = await seen.execute(
                    "SELECT pid FROM pg_stat_activity WHERE datname = %s"
                    " AND query = 'LISTEN fource_jobs' AND state = 'idle'",
                    (database,),
                )
                row = await cursor.fetchone()
                if row is not None:
                    return int(row[0])
                await asyncio.sleep(0.1)

    return await asyncio.wait_for(look(), 10)


async def app_role_is_idle(owner: str, app: str) -> None:
    """Returns once no backend of the app role is working: the job listener sits idle in LISTEN
    and a pooled connection is idle between passes. Seen twice in a row, so the gap between a
    wake-up's two passes does not count as rest."""
    database, role = make_url(owner).database, make_url(app).username

    async def look() -> None:
        async with await psycopg.AsyncConnection.connect(conninfo(owner), autocommit=True) as seen:
            quiet = 0
            while quiet < 2:
                cursor = await seen.execute(
                    "SELECT count(*) FROM pg_stat_activity"
                    " WHERE datname = %s AND usename = %s AND state <> 'idle'",
                    (database, role),
                )
                row = await cursor.fetchone()
                quiet = quiet + 1 if row is not None and row[0] == 0 else 0
                await asyncio.sleep(0.1)

    await asyncio.wait_for(look(), 10)


async def test_the_idle_wait_fails_when_the_probe_cannot_see_other_roles(
    postgres: tuple[str, str],
) -> None:
    # pg_stat_activity shows another role's `state` only to a superuser or a member of
    # pg_read_all_stats; for anyone else it is NULL, which must never count as idle. The app
    # role is such a role.
    _, app = postgres
    with pytest.raises(pytest.fail.Exception, match="pg_read_all_stats"):
        await app_role_is_idle(app, app)


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


@pytest.fixture
def worker_env(
    postgres: tuple[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, str]:
    """A migrated database, a throwaway signing key and scheduled checkpoints on, for the
    worker command. Sync on purpose: the CLI runs its own event loop."""
    owner, app = postgres
    upgrade(owner)
    monkeypatch.chdir(tmp_path)  # no .env from the repository, and data/ lands here
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)
    monkeypatch.setenv("FOURCE_SECRET_KEY", SECRET)
    monkeypatch.setenv("FOURCE_LEDGER_CHECKPOINT_MINUTES", "60")
    monkeypatch.setenv("FOURCE_DATABASE_URL", owner)
    assert cli.main(["ledger", "keygen"]) == 0
    return owner, app


def test_the_worker_refuses_to_run_as_the_owner(
    worker_env: tuple[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    # The same role check as the server's, before the worker takes any job: as the owner it
    # would run jobs in every organisation with row-level security off.
    owner, _ = worker_env
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 1
    out = capsys.readouterr().out
    password = make_url(owner).password
    assert "fource_app" in out and password is not None and password not in out
    with connect(owner) as connection:
        assert connection.execute(text("SELECT count(*) FROM jobs")).scalar() == 0


def test_the_worker_signs_a_checkpoint_as_the_app_role(
    worker_env: tuple[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Jobs run under row-level security: the scheduled checkpoint reads the ledger of the one
    # organisation it was enqueued for.
    _, app = worker_env
    monkeypatch.setenv("FOURCE_DATABASE_URL", app)
    monkeypatch.setattr("getpass.getpass", lambda prompt="": PASSWORD)
    assert cli.main(["create-user", "ada@example.com", "--role", "Viewer"]) == 0
    capsys.readouterr()
    assert cli.main(["worker", "--once"]) == 0
    assert "Ran 1 job attempt." in capsys.readouterr().out
    saved = tmp_path / "data" / "ledger" / "checkpoints"
    assert [file.name for file in saved.iterdir()] == ["default-0000000001.json"]


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


async def test_the_app_role_cannot_add_or_change_another_organisations_jobs(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    database = Database(postgres[1])
    try:
        async with database.org_session(orgs[1]) as session:
            await enqueue(session, "test.work")
    finally:
        await database.dispose()
    with connect(postgres[1]) as connection:
        set_org(connection, orgs[0])
        with pytest.raises(DBAPIError, match="row-level security"):
            connection.execute(
                text(
                    "INSERT INTO jobs (id, org_id, created_at, kind, payload, state, run_at,"
                    " attempts, max_attempts) VALUES (:id, :org, now(), 'test.work', '{}',"
                    " 'queued', now(), 0, 5)"
                ),
                {"id": new_id(), "org": orgs[1]},
            )
        connection.rollback()
        changed = connection.execute(
            text("UPDATE jobs SET state = 'failed' WHERE org_id = :org"), {"org": orgs[1]}
        )
        assert changed.rowcount == 0  # the other organisation's job is not even visible
        connection.rollback()
    with connect(postgres[1]) as connection:
        set_org(connection, orgs[1])
        states = connection.execute(text("SELECT state FROM jobs")).scalars().all()
    assert states == ["queued"]


async def test_two_workers_leave_one_recurring_occurrence_per_organisation_on_postgres(
    postgres: tuple[str, str],
    orgs: tuple[uuid.UUID, uuid.UUID],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    ran: list[uuid.UUID] = []

    async def note(session: AsyncSession, job: HeldJob) -> None:
        ran.append(job.org_id)

    hourly = Recurring("test.work", every=timedelta(hours=1))
    database = Database(postgres[1])
    try:
        workers = [Worker(database, {"test.work": Handler(note)}, recurring=[hourly]) for _ in "ab"]
        await asyncio.gather(*(worker.run_once() for worker in workers))
    finally:
        await database.dispose()
    assert sorted(ran) == sorted(orgs)  # each organisation's occurrence ran exactly once
    # The loser of the race must leave quietly: a failed step (an IntegrityError) is a warning.
    assert "failed" not in caplog.text
    with connect(postgres[1]) as connection:
        for org_id in orgs:
            set_org(connection, org_id)
            states = connection.execute(text("SELECT state FROM jobs ORDER BY state")).scalars()
            assert list(states) == ["done"]  # no second occurrence for this interval


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


async def test_a_running_worker_is_woken_and_records_a_failed_attempt_on_postgres(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    async def work(session: AsyncSession, job: HeldJob) -> None:
        if job.payload.get("fail"):
            raise ValueError("a line quoted from a document")

    database = Database(postgres[1])
    worker = Worker(database, {"test.work": Handler(work)}, poll_seconds=60)
    running = asyncio.create_task(worker.run())
    try:
        # Queue nothing before the listener is live and the worker is at rest (its start-up
        # passes are over), so that only a NOTIFY can bring the outcomes in under the 60 s poll.
        # (A slow machine only makes the wait longer.)
        await listener_pid(postgres[0])
        await app_role_is_idle(*postgres)
        async with database.org_session(orgs[0]) as session:
            good = await enqueue(session, "test.work")
        async with database.org_session(orgs[0]) as session:
            bad = await enqueue(session, "test.work", {"fail": True})

        async def outcome() -> dict[uuid.UUID, tuple[str, int, str | None]]:
            while True:  # only a wake-up gets here before the 60 s poll
                async with database.org_session(orgs[0]) as session:
                    rows = (await session.scalars(select(Job))).all()
                seen = {row.id: (row.state, row.attempts, row.last_error) for row in rows}
                if seen[good][0] == "done" and seen[bad][1] == 1 and seen[bad][0] == "queued":
                    return seen
                await asyncio.sleep(0.1)

        seen = await asyncio.wait_for(outcome(), 10)
    finally:
        worker.stop()
        await asyncio.wait_for(running, 10)
        await database.dispose()
    assert seen[good][0] == "done"
    assert seen[bad] == ("queued", 1, "ValueError")


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


async def test_a_notification_carries_no_organisation_id(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    # NOTIFY is per database and row-level security does not apply to it: any session of the
    # app role may LISTEN, with no organisation set, and would see who is active.
    _, app = postgres
    conninfo = make_url(app).set(drivername="postgresql").render_as_string(hide_password=False)
    database = Database(app)
    try:
        async with await psycopg.AsyncConnection.connect(conninfo, autocommit=True) as listener:
            await listener.execute("LISTEN fource_jobs")
            async with database.org_session(orgs[1]) as session:
                await enqueue(session, "test.work")
            received = [note async for note in listener.notifies(timeout=10, stop_after=1)]
    finally:
        await database.dispose()
    assert [(note.channel, note.payload) for note in received] == [("fource_jobs", "")]


async def test_the_listener_connects_again_after_its_backend_is_terminated(
    postgres: tuple[str, str], orgs: tuple[uuid.UUID, uuid.UUID]
) -> None:
    owner, app = postgres
    wakes: list[bool] = []
    first, second = asyncio.Event(), asyncio.Event()

    def on_wake() -> None:
        wakes.append(True)
        (first if len(wakes) == 1 else second).set()

    stop = asyncio.Event()
    listener = asyncio.create_task(listen_for_jobs(app, on_wake, stop, retry_seconds=0.2))
    try:
        await asyncio.wait_for(first.wait(), 10)  # listening
        pid = await listener_pid(owner)
        with connect(owner) as connection:
            connection.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})
        await asyncio.wait_for(second.wait(), 10)  # it listens again and wakes once more
        assert not listener.done()
    finally:
        stop.set()
        await asyncio.wait_for(listener, 10)
