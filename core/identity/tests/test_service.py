import asyncio
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from argon2 import PasswordHasher
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import new_id, set_clock
from fource.db import Base, Database, Org
from fource.identity import (
    LOCK_DURATION,
    MAX_FAILED_SIGNINS,
    AccountLocked,
    EmailTaken,
    InvalidCredentials,
    InvalidEmail,
    NotAuthenticated,
    RevokedToken,
    Role,
    SignedIn,
    TokenPayload,
    User,
    authenticate,
    create_user,
    needs_rehash,
    read_token,
    sign_in,
    sign_out,
    verify_password,
)

pytestmark = pytest.mark.anyio
SECRET = "s" * 40
PASSWORD = "correct horse battery"
TTL = timedelta(hours=8)


@pytest.fixture
async def org(tmp_path: Path) -> AsyncIterator[tuple[Database, uuid.UUID]]:
    database = Database(f"sqlite+aiosqlite:///{(tmp_path / 'identity.db').as_posix()}")
    async with database.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with database.session() as session:
        row = Org(slug="default", name="Default")
        session.add(row)
        await session.commit()
    async with database.org_session(row.id) as session:
        await create_user(session, email="Ada@Example.com", password=PASSWORD, roles=[Role.ADMIN])
    yield database, row.id
    await database.dispose()


@pytest.fixture
def clock() -> Iterator[list[datetime]]:
    moment = [datetime(2026, 10, 12, 9, 0, tzinfo=UTC)]
    set_clock(lambda: moment[0])
    yield moment
    set_clock(None)


async def attempt(org: tuple[Database, uuid.UUID], email: str, password: str) -> SignedIn:
    database, org_id = org
    async with database.org_session(org_id) as session:
        return await sign_in(session, email=email, password=password, secret=SECRET, ttl=TTL)


async def test_sign_in_returns_the_user_and_a_token(org: tuple[Database, uuid.UUID]) -> None:
    result = await attempt(org, "ada@example.com", PASSWORD)
    assert result.user.email == "ada@example.com"
    assert result.user.roles == ["Admin"]
    assert result.token.payload.user_id == result.user.id


async def test_email_case_and_spaces_dont_matter(org: tuple[Database, uuid.UUID]) -> None:
    result = await attempt(org, "  ADA@example.COM ", PASSWORD)
    assert result.user.email == "ada@example.com"


async def test_an_email_is_normalised_the_same_way_when_created_and_when_signing_in(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    async with database.org_session(org_id) as session:
        created = await create_user(
            session, email="  Grace@Example.COM  ", password=PASSWORD, roles=[Role.VIEWER]
        )
    assert created.email == "grace@example.com"
    for typed in ["grace@example.com", "GRACE@EXAMPLE.COM", "\tGrace@Example.com "]:
        assert (await attempt(org, typed, PASSWORD)).user.id == created.id


async def test_unknown_email_and_wrong_password_look_the_same(
    org: tuple[Database, uuid.UUID],
) -> None:
    with pytest.raises(InvalidCredentials) as unknown:
        await attempt(org, "nobody@example.com", PASSWORD)
    with pytest.raises(InvalidCredentials) as wrong:
        await attempt(org, "ada@example.com", "wrong horse battery")
    assert unknown.value.message == wrong.value.message


async def test_a_password_that_cannot_be_encoded_is_simply_wrong(
    org: tuple[Database, uuid.UUID],
) -> None:
    for email in ["ada@example.com", "nobody@example.com"]:
        with pytest.raises(InvalidCredentials):
            await attempt(org, email, "\ud800" * 12)


async def test_five_failures_lock_the_account_for_fifteen_minutes(
    org: tuple[Database, uuid.UUID], clock: list[datetime]
) -> None:
    for _ in range(MAX_FAILED_SIGNINS):
        with pytest.raises(InvalidCredentials):
            await attempt(org, "ada@example.com", "wrong horse battery")
    with pytest.raises(AccountLocked):
        await attempt(org, "ada@example.com", PASSWORD)
    clock[0] += LOCK_DURATION + timedelta(seconds=1)
    assert (await attempt(org, "ada@example.com", PASSWORD)).user.failed_signins == 0


async def test_a_success_resets_the_failure_count(org: tuple[Database, uuid.UUID]) -> None:
    for _ in range(MAX_FAILED_SIGNINS - 1):
        with pytest.raises(InvalidCredentials):
            await attempt(org, "ada@example.com", "wrong horse battery")
    await attempt(org, "ada@example.com", PASSWORD)
    with pytest.raises(InvalidCredentials):
        await attempt(org, "ada@example.com", "wrong horse battery")
    await attempt(org, "ada@example.com", PASSWORD)  # one failure, not five: not locked


async def test_wrong_guesses_sent_together_still_lock_the_account(
    org: tuple[Database, uuid.UUID],
) -> None:
    guesses = [attempt(org, "ada@example.com", "wrong horse battery") for _ in range(10)]
    outcomes = await asyncio.gather(*guesses, return_exceptions=True)
    assert all(isinstance(outcome, (InvalidCredentials, AccountLocked)) for outcome in outcomes)
    with pytest.raises(AccountLocked):
        await attempt(org, "ada@example.com", PASSWORD)


async def test_a_hash_with_older_parameters_is_upgraded_on_sign_in(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(PASSWORD)
    async with database.org_session(org_id) as session:
        user = await session.scalar(select(User))
        assert user is not None
        user.password_hash = weak
    assert needs_rehash(weak)
    result = await attempt(org, "ada@example.com", PASSWORD)
    assert result.user.password_hash != weak
    assert not needs_rehash(result.user.password_hash)
    assert verify_password(result.user.password_hash, PASSWORD)


async def test_a_signed_in_token_authenticates_until_signed_out(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    payload = (await attempt(org, "ada@example.com", PASSWORD)).token.payload
    async with database.org_session(org_id) as session:
        assert (await authenticate(session, payload)).email == "ada@example.com"
        await sign_out(session, payload)
    async with database.org_session(org_id) as session:
        with pytest.raises(NotAuthenticated):
            await authenticate(session, payload)


async def test_signing_out_twice_is_fine_and_the_token_stays_revoked(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    payload = (await attempt(org, "ada@example.com", PASSWORD)).token.payload
    for _ in range(2):
        async with database.org_session(org_id) as session:
            await sign_out(session, payload)
    async with database.org_session(org_id) as session:
        with pytest.raises(NotAuthenticated):
            await authenticate(session, payload)
        assert len((await session.scalars(select(RevokedToken))).all()) == 1


async def test_a_sign_out_that_loses_a_race_still_succeeds(
    org: tuple[Database, uuid.UUID], monkeypatch: pytest.MonkeyPatch
) -> None:
    database, org_id = org
    payload = (await attempt(org, "ada@example.com", PASSWORD)).token.payload
    async with database.org_session(org_id) as session:
        await sign_out(session, payload)  # the sign-out that wins the race

    async def not_yet_visible(session: AsyncSession, token_id: uuid.UUID) -> bool:
        return False  # the loser looked before the winner committed

    monkeypatch.setattr("fource.identity.service._is_revoked", not_yet_visible)
    async with database.org_session(org_id) as session:
        await sign_out(session, payload)
        assert len((await session.scalars(select(RevokedToken))).all()) == 1


async def test_signing_out_stores_the_expiry_of_the_payload_read_from_the_token(
    org: tuple[Database, uuid.UUID],
) -> None:
    # The real clock: PyJWT reads the token's times against the system clock, not ours.
    database, org_id = org
    token = (await attempt(org, "ada@example.com", PASSWORD)).token.token
    payload = read_token(token, SECRET)
    async with database.org_session(org_id) as session:
        await sign_out(session, payload)
    async with database.org_session(org_id) as session:
        stored = await session.scalar(select(RevokedToken))
        assert stored is not None
        assert (stored.token_id, stored.expires_at) == (payload.token_id, payload.expires_at)
        with pytest.raises(NotAuthenticated):
            await authenticate(session, payload)


async def test_signing_out_forgets_revocations_that_have_expired(
    org: tuple[Database, uuid.UUID], clock: list[datetime]
) -> None:
    database, org_id = org
    user_id = (await attempt(org, "ada@example.com", PASSWORD)).user.id
    early = TokenPayload(user_id, org_id, new_id(), clock[0] + timedelta(hours=1))
    late = TokenPayload(user_id, org_id, new_id(), clock[0] + timedelta(hours=9))
    async with database.org_session(org_id) as session:
        await sign_out(session, early)
    clock[0] += timedelta(hours=2)
    async with database.org_session(org_id) as session:
        await sign_out(session, late)
    async with database.org_session(org_id) as session:
        kept = (await session.scalars(select(RevokedToken.token_id))).all()
    assert kept == [late.token_id]


async def test_a_deactivated_users_token_is_refused(org: tuple[Database, uuid.UUID]) -> None:
    database, org_id = org
    result = await attempt(org, "ada@example.com", PASSWORD)
    async with database.org_session(org_id) as session:
        user = await session.get(User, result.user.id)
        assert user is not None
        user.is_active = False
    async with database.org_session(org_id) as session:
        with pytest.raises(NotAuthenticated):
            await authenticate(session, result.token.payload)
    with pytest.raises(InvalidCredentials):
        await attempt(org, "ada@example.com", PASSWORD)


async def test_a_token_for_another_organisation_is_refused(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    payload = (await attempt(org, "ada@example.com", PASSWORD)).token.payload
    elsewhere = TokenPayload(payload.user_id, new_id(), payload.token_id, payload.expires_at)
    async with database.org_session(org_id) as session:
        with pytest.raises(NotAuthenticated):
            await authenticate(session, elsewhere)


async def test_emails_are_unique_and_must_look_like_emails(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    async with database.org_session(org_id) as session:
        with pytest.raises(EmailTaken):
            await create_user(session, email="ADA@example.com", password=PASSWORD, roles=[])
    async with database.org_session(org_id) as session:
        with pytest.raises(EmailTaken):
            await create_user(session, email="  Ada@Example.com ", password=PASSWORD, roles=[])
    async with database.org_session(org_id) as session:
        with pytest.raises(InvalidEmail):
            await create_user(session, email="not-an-email", password=PASSWORD, roles=[])


async def test_an_email_that_cannot_be_encoded_is_no_email_and_no_user(
    org: tuple[Database, uuid.UUID],
) -> None:
    database, org_id = org
    with pytest.raises(InvalidCredentials):
        await attempt(org, "\ud800@example.com", PASSWORD)
    async with database.org_session(org_id) as session:
        with pytest.raises(InvalidEmail):
            await create_user(session, email="\ud800@example.com", password=PASSWORD, roles=[])


async def test_unknown_roles_are_refused(org: tuple[Database, uuid.UUID]) -> None:
    database, org_id = org
    async with database.org_session(org_id) as session:
        with pytest.raises(ValueError):
            await create_user(session, email="b@example.com", password=PASSWORD, roles=["Boss"])
