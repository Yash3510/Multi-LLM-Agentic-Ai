from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import now
from fource.identity.errors import (
    AccountLocked,
    EmailTaken,
    InvalidCredentials,
    InvalidEmail,
    NotAuthenticated,
)
from fource.identity.models import RevokedToken, User
from fource.identity.passwords import (
    hash_password,
    needs_rehash,
    rehash,
    timing_hash,
    verify_password,
)
from fource.identity.roles import Role
from fource.identity.tokens import IssuedToken, TokenPayload, issue_token

MAX_FAILED_SIGNINS = 5
LOCK_DURATION = timedelta(minutes=15)
_WRONG = "The email or password is wrong."
_LOCKED = "Too many failed sign-ins. Try again in 15 minutes."
_SIGN_IN_AGAIN = "Sign in again."


@dataclass(frozen=True)
class SignedIn:
    user: User
    token: IssuedToken


def normalise_email(email: str) -> str:
    return email.strip().lower()


def _storable(text: str) -> bool:
    """False for text with a lone surrogate: it has no UTF-8 form, so the database refuses it."""
    try:
        text.encode()
    except UnicodeEncodeError:
        return False
    return True


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    roles: Iterable[Role | str],
    display_name: str = "",
) -> User:
    address = normalise_email(email)
    local, _, domain = address.partition("@")
    if not local or "." not in domain or not _storable(address):
        raise InvalidEmail("That doesn't look like an email address.")
    granted = [Role(role).value for role in roles]
    if await session.scalar(select(User.id).where(User.email == address)) is not None:
        raise EmailTaken("A user with that email already exists.")
    user = User(
        email=address,
        display_name=display_name,
        password_hash=hash_password(password),
        roles=granted,
        is_active=True,
        failed_signins=0,
        locked_until=None,
    )
    session.add(user)
    await session.flush()
    return user


async def _count_failure(session: AsyncSession, user: User, current: datetime) -> None:
    """Add one failed sign-in and lock the account at the limit.

    The database adds the one, so guesses sent together can't overwrite each other's count.
    The in-memory user isn't updated; the caller raises next and doesn't use it again.
    """
    this_user = User.id == user.id
    unchanged = {"synchronize_session": False}
    failures = await session.scalar(
        update(User)
        .where(this_user)
        .values(failed_signins=User.failed_signins + 1)
        .returning(User.failed_signins),
        execution_options=unchanged,
    )
    if failures is not None and failures >= MAX_FAILED_SIGNINS:
        lock = update(User).where(this_user)
        lock = lock.values(failed_signins=0, locked_until=current + LOCK_DURATION)
        await session.execute(lock, execution_options=unchanged)


async def sign_in(
    session: AsyncSession, *, email: str, password: str, secret: str, ttl: timedelta
) -> SignedIn:
    address = normalise_email(email)
    user = None
    if _storable(address):  # otherwise it can't be anyone's email
        user = await session.scalar(select(User).where(User.email == address))
    if user is None or not user.is_active:
        verify_password(timing_hash(), password)  # the same work as a real attempt
        raise InvalidCredentials(_WRONG)
    current = now()
    if user.locked_until is not None and user.locked_until > current:
        raise AccountLocked(_LOCKED)
    if not verify_password(user.password_hash, password):
        await _count_failure(session, user, current)
        await session.commit()  # the count must survive the error raised next
        raise InvalidCredentials(_WRONG)
    user.failed_signins = 0
    user.locked_until = None
    if needs_rehash(user.password_hash):
        user.password_hash = rehash(password)
    token = issue_token(user_id=user.id, org_id=user.org_id, secret=secret, ttl=ttl)
    return SignedIn(user=user, token=token)


async def authenticate(session: AsyncSession, payload: TokenPayload) -> User:
    """The active user a valid, unrevoked token belongs to; otherwise NotAuthenticated."""
    revoked = select(RevokedToken.id).where(RevokedToken.token_id == payload.token_id)
    if await session.scalar(revoked) is not None:
        raise NotAuthenticated(_SIGN_IN_AGAIN)
    user = await session.get(User, payload.user_id)
    if user is None or not user.is_active or user.org_id != payload.org_id:
        raise NotAuthenticated(_SIGN_IN_AGAIN)
    return user


async def sign_out(session: AsyncSession, payload: TokenPayload) -> None:
    await session.execute(delete(RevokedToken).where(RevokedToken.expires_at < now()))
    session.add(RevokedToken(token_id=payload.token_id, expires_at=payload.expires_at))
    await session.flush()
