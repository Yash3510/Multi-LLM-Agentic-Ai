import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from fource.common import Settings
from fource.db import Database
from fource.identity import NotAuthenticated, TokenPayload, User, authenticate, read_token
from fource.server.errors import CsrfFailed

TOKEN_COOKIE = "fource_token"
CSRF_COOKIE = "fource_csrf"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def settings_of(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def database_of(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


def token_of(request: Request) -> str:
    """The bearer token, or the cookie one; a cookie can't change anything without CSRF."""
    header = request.headers.get("authorization", "")
    if header[:7].lower() == "bearer ":
        return header[7:].strip()
    token = request.cookies.get(TOKEN_COOKIE, "")
    if token and request.method not in SAFE_METHODS:
        sent = request.headers.get(CSRF_HEADER, "")
        expected = request.cookies.get(CSRF_COOKIE, "")
        # As bytes: compare_digest raises TypeError for non-ASCII str, and a header can hold any.
        if not expected or not secrets.compare_digest(sent.encode(), expected.encode()):
            raise CsrfFailed("Reload the page and try again.")
    if not token:
        raise NotAuthenticated("Sign in first.")
    return token


@dataclass(frozen=True)
class Auth:
    user: User
    payload: TokenPayload


async def signed_in(request: Request) -> Auth:
    """The signed-in user, checked against the database on every request (ADR-0038)."""
    token = token_of(request)
    payload = read_token(token, settings_of(request).secret_key.get_secret_value())
    async with database_of(request).org_session(payload.org_id) as session:
        user = await authenticate(session, payload)
    return Auth(user=user, payload=payload)


SignedIn = Annotated[Auth, Depends(signed_in)]
