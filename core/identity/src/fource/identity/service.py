from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, select
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
    if not local or "." not in domain:
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


async def sign_in(
    session: AsyncSession, *, email: str, password: str, secret: str, ttl: timedelta
) -> SignedIn:
    user = await session.scalar(select(User).where(User.email == normalise_email(email)))
    if user is None or not user.is_active:
        verify_password(timing_hash(), password)  # the same work as a real attempt
        raise InvalidCredentials(_WRONG)
    current = now()
    if user.locked_until is not None and user.locked_until > current:
        raise AccountLocked(_LOCKED)
    if not verify_password(user.password_hash, password):
        user.failed_signins += 1
        if user.failed_signins >= MAX_FAILED_SIGNINS:
            user.failed_signins = 0
            user.locked_until = current + LOCK_DURATION
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
