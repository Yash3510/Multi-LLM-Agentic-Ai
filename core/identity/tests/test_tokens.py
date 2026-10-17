import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from fource.common import new_id, set_clock
from fource.identity import NotAuthenticated, issue_token, read_token

SECRET = "s" * 40
USER, ORG = new_id(), new_id()


def test_a_token_round_trips() -> None:
    issued = issue_token(user_id=USER, org_id=ORG, secret=SECRET, ttl=timedelta(hours=8))
    payload = read_token(issued.token, SECRET)
    assert (payload.user_id, payload.org_id) == (USER, ORG)
    assert payload.token_id == issued.payload.token_id
    assert payload.expires_at == issued.payload.expires_at.replace(microsecond=0)


def test_each_token_has_its_own_id() -> None:
    first = issue_token(user_id=USER, org_id=ORG, secret=SECRET, ttl=timedelta(hours=1))
    second = issue_token(user_id=USER, org_id=ORG, secret=SECRET, ttl=timedelta(hours=1))
    assert first.payload.token_id != second.payload.token_id


def test_an_expired_token_is_refused() -> None:
    set_clock(lambda: datetime.now(UTC) - timedelta(hours=9))
    try:
        issued = issue_token(user_id=USER, org_id=ORG, secret=SECRET, ttl=timedelta(hours=8))
    finally:
        set_clock(None)
    with pytest.raises(NotAuthenticated):
        read_token(issued.token, SECRET)


def test_a_token_signed_with_another_key_is_refused() -> None:
    issued = issue_token(user_id=USER, org_id=ORG, secret="o" * 40, ttl=timedelta(hours=1))
    with pytest.raises(NotAuthenticated):
        read_token(issued.token, SECRET)


def test_an_unsigned_token_is_refused() -> None:
    forged = jwt.encode(
        {"sub": str(USER), "org": str(ORG), "jti": str(uuid.uuid4()), "iat": 0, "exp": 2**40},
        "",  # "none" takes an empty key
        algorithm="none",
    )
    with pytest.raises(NotAuthenticated):
        read_token(forged, SECRET)


def test_a_token_missing_fields_is_refused() -> None:
    thin = jwt.encode({"sub": str(USER), "exp": 2**40}, SECRET, algorithm="HS256")
    with pytest.raises(NotAuthenticated):
        read_token(thin, SECRET)


def test_garbage_is_refused() -> None:
    with pytest.raises(NotAuthenticated):
        read_token("not.a.token", SECRET)
