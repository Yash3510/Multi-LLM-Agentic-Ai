import hashlib
import hmac
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fource.common import now
from fource.identity.errors import (
    AccountLocked,
    EmailTaken,
    InvalidCredentials,
    InvalidDisplayName,
    InvalidEmail,
    NotAuthenticated,
)
from fource.identity.models import DISPLAY_NAME_LENGTH, EMAIL_LENGTH, RevokedToken, User
from fource.identity.passwords import (
    hash_password,
    needs_rehash,
    rehash,
    timing_hash,
    verify_password,
)
from fource.identity.roles import Role
from fource.identity.tokens import IssuedToken, TokenPayload, issue_token
from fource.ledger import ANONYMOUS, SYSTEM, EntryType, append, format_time, user_actor

MAX_FAILED_SIGNINS = 5
LOCK_DURATION = timedelta(minutes=15)
_WRONG = "The email or password is wrong."
_LOCKED = "Too many failed sign-ins. Try again in 15 minutes."
_SIGN_IN_AGAIN = "Sign in again."
_UNKNOWN_EMAIL_CONTEXT = b"4ce-ledger-unknown-email-v1"


@dataclass(frozen=True)
class SignedIn:
    user: User
    token: IssuedToken


def normalise_email(email: str) -> str:
    return email.strip().lower()


def unknown_email_digest(email: str, secret: str) -> str:
    """The keyed hash the ledger keeps of an email nobody here has (ADR-0039): 64 lower-case hex.

    A plain SHA-256 of a common address can be found by guessing and hashing, so this is an
    HMAC-SHA256 of the normalised address. Whoever holds the installation secret can confirm
    an address; whoever has only the ledger or an evidence pack cannot. The key is derived
    from the secret for this one purpose, so the token-signing secret is never used directly.
    Rotating `FOURCE_SECRET_KEY` means digests written earlier can no longer be confirmed.
    """
    key = hmac.new(secret.encode("utf-8"), _UNKNOWN_EMAIL_CONTEXT, hashlib.sha256).digest()
    address = normalise_email(email).encode("utf-8", "surrogatepass")
    return hmac.new(key, address, hashlib.sha256).hexdigest()


def _storable(text: str) -> bool:
    """False for text the database refuses: PostgreSQL can't hold NUL, and a lone surrogate
    has no UTF-8 form."""
    if "\x00" in text:
        return False
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
    if not local or "." not in domain or len(address) > EMAIL_LENGTH or not _storable(address):
        raise InvalidEmail("That doesn't look like an email address.")
    if len(display_name) > DISPLAY_NAME_LENGTH or not _storable(display_name):
        raise InvalidDisplayName(
            f"A display name is plain text of up to {DISPLAY_NAME_LENGTH} characters."
        )
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
    refs = {"user": str(user.id), "roles": ",".join(granted)}
    await append(session, EntryType.USER_CREATE, actor=SYSTEM, refs=refs)
    return user


async def _count_failure(session: AsyncSession, user: User, current: datetime) -> bool:
    """Add one failed sign-in and lock the account at the limit; True if this one locked it.

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
        return True
    return False


async def _record_failure(
    session: AsyncSession, address: str, user: User | None, reason: str, secret: str
) -> None:
    """A failed sign-in. An unknown address is kept only as a keyed hash: the ledger can never
    be erased, so it holds no address that belongs to nobody here (ADR-0039)."""
    refs = {"reason": reason}
    digest = None
    if user is None:
        digest = unknown_email_digest(address, secret)
    else:
        refs["user"] = str(user.id)
    await append(
        session, EntryType.SIGNIN_FAILURE, actor=ANONYMOUS, refs=refs, inputs_sha256=digest
    )


async def sign_in(
    session: AsyncSession, *, email: str, password: str, secret: str, ttl: timedelta
) -> SignedIn:
    address = normalise_email(email)
    user = None
    if _storable(address):  # otherwise it can't be anyone's email
        user = await session.scalar(select(User).where(User.email == address))
    if user is None or not user.is_active:
        verify_password(timing_hash(), password)  # the same work as a real attempt
        reason = "unknown_email" if user is None else "inactive"
        await _record_failure(session, address, user, reason, secret)
        await session.commit()  # the entry must survive the error raised next
        raise InvalidCredentials(_WRONG)
    current = now()
    if user.locked_until is not None and user.locked_until > current:
        await _record_failure(session, address, user, "locked", secret)
        await session.commit()
        raise AccountLocked(_LOCKED)
    if not verify_password(user.password_hash, password):
        locked = await _count_failure(session, user, current)
        await _record_failure(session, address, user, "wrong_password", secret)
        if locked:
            until = format_time(current + LOCK_DURATION)
            refs = {"user": str(user.id), "until": until}
            await append(session, EntryType.LOCKOUT, actor=SYSTEM, refs=refs)
        await session.commit()  # the count and the entries must survive the error raised next
        raise InvalidCredentials(_WRONG)
    user.failed_signins = 0
    user.locked_until = None
    if needs_rehash(user.password_hash):
        user.password_hash = rehash(password)
    token = issue_token(user_id=user.id, org_id=user.org_id, secret=secret, ttl=ttl)
    refs = {"user": str(user.id), "token": str(token.payload.token_id)}
    await append(session, EntryType.SIGNIN_SUCCESS, actor=user_actor(user.id), refs=refs)
    return SignedIn(user=user, token=token)


async def _is_revoked(session: AsyncSession, token_id: uuid.UUID) -> bool:
    found = await session.scalar(select(RevokedToken.id).where(RevokedToken.token_id == token_id))
    return found is not None


async def authenticate(session: AsyncSession, payload: TokenPayload) -> User:
    """The active user a valid, unrevoked token belongs to; otherwise NotAuthenticated."""
    if await _is_revoked(session, payload.token_id):
        raise NotAuthenticated(_SIGN_IN_AGAIN)
    user = await session.get(User, payload.user_id)
    if user is None or not user.is_active or user.org_id != payload.org_id:
        raise NotAuthenticated(_SIGN_IN_AGAIN)
    return user


async def sign_out(session: AsyncSession, payload: TokenPayload) -> None:
    """Revoke the token; signing out a token that is already revoked does nothing."""
    await session.execute(delete(RevokedToken).where(RevokedToken.expires_at < now()))
    if await _is_revoked(session, payload.token_id):
        return
    refs = {"user": str(payload.user_id), "token": str(payload.token_id)}
    try:
        async with session.begin_nested():
            session.add(RevokedToken(token_id=payload.token_id, expires_at=payload.expires_at))
            # Inside the savepoint, so a sign-out that loses the race records nothing.
            await append(session, EntryType.SIGNOUT, actor=user_actor(payload.user_id), refs=refs)
    except IntegrityError:
        pass  # a sign-out of the same token won the race; the token is revoked either way
