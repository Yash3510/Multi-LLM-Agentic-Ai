import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError, ProgrammingError

from fource.db import table_missing
from fource.identity import MAX_PASSWORD_LENGTH, User, sign_in, sign_out
from fource.server.deps import CSRF_COOKIE, TOKEN_COOKIE, SignedIn, database_of, settings_of
from fource.server.errors import SetupIncomplete, declared

router = APIRouter(prefix="/api/auth", tags=["auth"])


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


@router.post("/signin", response_model=SignInOut, responses=declared(401, 422, 423, 503))
async def sign_in_route(body: SignInRequest, request: Request, response: Response) -> SignInOut:
    settings, database = settings_of(request), database_of(request)
    not_set_up = SetupIncomplete("The database isn't set up yet: run `just migrate`.")
    ttl = timedelta(minutes=settings.token_ttl_minutes)
    try:
        org_id = await database.org_id(settings.org)
        if org_id is None:
            raise not_set_up
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
