import math
import re
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError, ProgrammingError

from fource.common import now
from fource.db import table_missing
from fource.identity import MAX_PASSWORD_LENGTH, User, record_throttled, sign_in, sign_out
from fource.live import LiveUnavailable
from fource.server.deps import (
    CSRF_COOKIE,
    TOKEN_COOKIE,
    SignedIn,
    database_of,
    live_of,
    settings_of,
)
from fource.server.errors import RateLimited, RateLimitUnavailable, SetupIncomplete, declared

router = APIRouter(prefix="/api/auth", tags=["auth"])
SIGNIN_WINDOW = timedelta(minutes=1)
_NOT_IN_A_KEY = re.compile(r"[^A-Za-z0-9_.:-]")


class SignInRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    roles: list[str]
    org: str


class SignInOut(BaseModel):
    user: UserOut
    token: str
    expires_at: datetime


def user_out(user: User, org: str) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=list(user.roles),
        org=org,
    )


async def _count_attempt(request: Request, org_id: uuid.UUID) -> None:
    """Counts the sign-in against its client address before any password is checked or anything
    is written (ADR-0026). Over the limit: 429. The attempt that first goes over records the
    throttling in the ledger, once per window. Redis down: 503, because a limit that can't be
    checked is not a pass. The per-account lockout still applies to every attempt let through."""
    settings, database = settings_of(request), database_of(request)
    address = request.client.host if request.client else "unknown"
    key = "signin:" + _NOT_IN_A_KEY.sub("_", address)[:150]
    limit = settings.signin_attempts_per_minute
    try:
        hit = await live_of(request).limits.hit(org_id, key, limit=limit, window=SIGNIN_WINDOW)
    except LiveUnavailable as error:
        raise RateLimitUnavailable(
            "Signing in is paused: the server can't check its rate limit. Try again in a minute."
        ) from error
    if hit.allowed:
        return
    if hit.count == limit + 1:
        async with database.org_session(org_id) as session:
            await record_throttled(
                session,
                address=address,
                secret=settings.secret_key.get_secret_value(),
                limit=limit,
                until=now() + hit.retry_after,
            )
    wait = max(1, math.ceil(hit.retry_after.total_seconds()))
    raise RateLimited(
        "Too many sign-in attempts from this address. Try again in a minute.", retry_after=wait
    )


@router.post("/signin", response_model=SignInOut, responses=declared(401, 422, 423, 429, 503))
async def sign_in_route(body: SignInRequest, request: Request, response: Response) -> SignInOut:
    settings, database = settings_of(request), database_of(request)
    not_set_up = SetupIncomplete("The database isn't set up yet: run `just migrate`.")
    ttl = timedelta(minutes=settings.token_ttl_minutes)
    try:
        org_id = await database.org_id(settings.org)
        if org_id is None:
            raise not_set_up
        await _count_attempt(request, org_id)
        async with database.org_session(org_id) as session:
            result = await sign_in(
                session,
                email=body.email,
                password=body.password,
                secret=settings.secret_key.get_secret_value(),
                ttl=ttl,
            )
    except (OperationalError, ProgrammingError) as error:
        # No organisations table, or (a database migrated only to 0003) no ledger tables,
        # which sign-in writes. An unreachable database stays a plain 500.
        if not table_missing(error):
            raise
        raise not_set_up from error
    secure = request.url.scheme == "https"
    seconds = int(ttl.total_seconds())
    response.set_cookie(
        TOKEN_COOKIE,
        result.token.token,
        max_age=seconds,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_urlsafe(32),
        max_age=seconds,
        secure=secure,
        samesite="strict",
        path="/",
    )
    return SignInOut(
        user=user_out(result.user, settings.org),
        token=result.token.token,
        expires_at=result.token.payload.expires_at,
    )


@router.get("/session", response_model=UserOut, responses=declared(401))
async def session_route(auth: SignedIn, request: Request) -> UserOut:
    return user_out(auth.user, settings_of(request).org)


@router.post("/signout", status_code=204, responses=declared(401, 403))
async def sign_out_route(auth: SignedIn, request: Request) -> Response:
    async with database_of(request).org_session(auth.payload.org_id) as session:
        await sign_out(session, auth.payload)
    response = Response(status_code=204)
    response.delete_cookie(TOKEN_COOKIE, path="/")
    response.delete_cookie(CSRF_COOKIE, path="/")
    return response
