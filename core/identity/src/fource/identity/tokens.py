import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from fource.common import new_id, now
from fource.identity.errors import NotAuthenticated

ALGORITHM = "HS256"
_REQUIRED = ["sub", "org", "jti", "iat", "exp"]
_SIGN_IN_AGAIN = "Sign in again."


@dataclass(frozen=True)
class TokenPayload:
    user_id: uuid.UUID
    org_id: uuid.UUID
    token_id: uuid.UUID
    expires_at: datetime


@dataclass(frozen=True)
class IssuedToken:
    token: str
    payload: TokenPayload


def issue_token(
    *, user_id: uuid.UUID, org_id: uuid.UUID, secret: str, ttl: timedelta
) -> IssuedToken:
    issued_at = now()
    payload = TokenPayload(user_id, org_id, new_id(), issued_at + ttl)
    body = {
        "sub": str(user_id),
        "org": str(org_id),
        "jti": str(payload.token_id),
        "iat": issued_at,
        "exp": payload.expires_at,
    }
    return IssuedToken(jwt.encode(body, secret, algorithm=ALGORITHM), payload)


def _text(body: dict[str, Any], name: str) -> str:
    value = body[name]
    if not isinstance(value, str):
        raise NotAuthenticated(_SIGN_IN_AGAIN)
    return value


def read_token(token: str, secret: str) -> TokenPayload:
    """The payload of a valid token; anything else (expired, forged, other key, wrong
    algorithm, missing or mistyped fields) is NotAuthenticated."""
    try:
        body = jwt.decode(token, secret, algorithms=[ALGORITHM], options={"require": _REQUIRED})
        return TokenPayload(
            user_id=uuid.UUID(_text(body, "sub")),
            org_id=uuid.UUID(_text(body, "org")),
            token_id=uuid.UUID(_text(body, "jti")),
            expires_at=datetime.fromtimestamp(body["exp"], UTC),
        )
    # OverflowError, OSError: a signed but absurd expiry can overflow the date (Windows: OSError).
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError, OSError) as error:
        raise NotAuthenticated(_SIGN_IN_AGAIN) from error
