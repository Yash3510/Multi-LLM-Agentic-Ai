import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from starlette.exceptions import HTTPException as StarletteHTTPException

from fource.common import FourceError, Settings
from fource.db import CrossOrgWrite, Database
from fource.identity import (
    AccountLocked,
    EmailTaken,
    InvalidCredentials,
    InvalidDisplayName,
    InvalidEmail,
    NotAuthenticated,
    WeakPassword,
)
from fource.ledger import EntryType, read_entries
from fource.server.errors import CsrfFailed, SetupIncomplete
from fource.server.main import app_factory, create_app

pytestmark = pytest.mark.anyio
PASSWORD = "correct horse battery"


async def sign_in(client: httpx.AsyncClient, password: str = PASSWORD) -> httpx.Response:
    return await client.post(
        "/api/auth/signin", json={"email": "ada@example.com", "password": password}
    )


async def get_from(app: FastAPI, path: str, *, raise_exceptions: bool = True) -> httpx.Response:
    """One request to an app of its own; the engine is closed afterwards."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=raise_exceptions)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(path)
    finally:
        await app.state.database.dispose()


async def test_health_reports_the_database(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health")
    assert (response.status_code, response.json()) == (200, {"status": "ok", "database": "ok"})


async def test_health_reports_an_unreachable_database(settings: Settings) -> None:
    unreachable = SecretStr("postgresql+psycopg://nobody:wrong@127.0.0.1:1/none")
    app = create_app(settings.model_copy(update={"database_url": unreachable}))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    await app.state.database.dispose()
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable"}


async def test_sign_in_sets_both_cookies_and_returns_a_token(client: httpx.AsyncClient) -> None:
    response = await sign_in(client)
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "ada@example.com"
    assert body["user"]["roles"] == ["Admin"] and body["user"]["org"] == "default"
    assert body["token"] and body["expires_at"]
    cookies = response.headers.get_list("set-cookie")
    token_cookie = next(c for c in cookies if c.startswith("fource_token="))
    csrf_cookie = next(c for c in cookies if c.startswith("fource_csrf="))
    assert "HttpOnly" in token_cookie and "SameSite=strict" in token_cookie
    assert "HttpOnly" not in csrf_cookie and "SameSite=strict" in csrf_cookie


async def test_the_session_reads_the_cookie(client: httpx.AsyncClient) -> None:
    await sign_in(client)
    response = await client.get("/api/auth/session")
    assert (response.status_code, response.json()["email"]) == (200, "ada@example.com")


async def test_the_session_reads_a_bearer_token(client: httpx.AsyncClient) -> None:
    token = (await sign_in(client)).json()["token"]
    client.cookies.clear()
    response = await client.get("/api/auth/session", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


async def test_signing_out_by_cookie_needs_the_csrf_header(client: httpx.AsyncClient) -> None:
    await sign_in(client)
    refused = await client.post("/api/auth/signout")
    assert (refused.status_code, refused.json()["error"]["code"]) == (403, "csrf_failed")
    header = {"X-CSRF-Token": client.cookies["fource_csrf"]}
    assert (await client.post("/api/auth/signout", headers=header)).status_code == 204


async def test_signing_out_by_bearer_needs_no_csrf_and_revokes(client: httpx.AsyncClient) -> None:
    token = (await sign_in(client)).json()["token"]
    client.cookies.clear()
    bearer = {"Authorization": f"Bearer {token}"}
    assert (await client.post("/api/auth/signout", headers=bearer)).status_code == 204
    after = await client.get("/api/auth/session", headers=bearer)
    assert (after.status_code, after.json()["error"]["code"]) == (401, "not_authenticated")


async def test_a_wrong_password_is_invalid_credentials(client: httpx.AsyncClient) -> None:
    response = await sign_in(client, "wrong horse battery")
    assert (response.status_code, response.json()["error"]["code"]) == (401, "invalid_credentials")


async def test_the_sixth_attempt_after_five_failures_is_locked(client: httpx.AsyncClient) -> None:
    for _ in range(5):
        await sign_in(client, "wrong horse battery")
    response = await sign_in(client)
    assert (response.status_code, response.json()["error"]["code"]) == (423, "account_locked")


async def test_no_token_is_not_authenticated(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/auth/session")
    assert (response.status_code, response.json()["error"]["code"]) == (401, "not_authenticated")


async def test_a_huge_password_is_refused_before_hashing(client: httpx.AsyncClient) -> None:
    response = await sign_in(client, "x" * 2_000_000)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "validation_failed")


async def test_the_contract_is_published_and_the_doc_pages_are_off(
    client: httpx.AsyncClient,
) -> None:
    contract = (await client.get("/api/openapi.json")).json()
    for path in ("/api/health", "/api/auth/signin", "/api/auth/session", "/api/auth/signout"):
        assert path in contract["paths"]
    assert (await client.get("/docs")).status_code == 404
    assert (await client.get("/redoc")).status_code == 404


KNOWN_ERRORS: list[tuple[type[FourceError], str, int]] = [
    (InvalidCredentials, "invalid_credentials", 401),
    (AccountLocked, "account_locked", 423),
    (NotAuthenticated, "not_authenticated", 401),
    (CsrfFailed, "csrf_failed", 403),
    (InvalidDisplayName, "validation_failed", 422),
    (WeakPassword, "weak_password", 422),
    (InvalidEmail, "invalid_email", 422),
    (EmailTaken, "email_taken", 409),
    (CrossOrgWrite, "cross_org_write", 403),
    (SetupIncomplete, "setup_incomplete", 503),
]


@pytest.mark.parametrize(("error", "code", "status"), KNOWN_ERRORS)
async def test_every_known_error_keeps_its_status_in_the_envelope(
    settings: Settings, error: type[FourceError], code: str, status: int
) -> None:
    app = create_app(settings)

    async def fail() -> None:
        raise error("Something to act on.")

    app.add_api_route("/api/fail", fail)
    response = await get_from(app, "/api/fail")
    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": "Something to act on."}}


async def test_an_unexpected_error_is_a_generic_500_with_no_detail(settings: Settings) -> None:
    app = create_app(settings)

    async def explode() -> None:
        raise RuntimeError("password=hunter2 at /srv/fource/secret.py")

    app.add_api_route("/api/explode", explode)
    response = await get_from(app, "/api/explode", raise_exceptions=False)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    for leaked in ("hunter2", "secret.py", "RuntimeError", "Traceback"):
        assert leaked not in response.text


@pytest.mark.parametrize(
    "content",
    [
        b'{"email": "ada@example.com", "password": ["hunter2hunter2"]}',
        b'{"email": ["ada@example.com"], "password": "hunter2hunter2"}',
        b'{"password": "hunter2hunter2"}',
        b'["hunter2hunter2"]',
        b'"hunter2hunter2"',
        b'{"email": "ada@example.com", "password": "hunter2hunter2"',
        b'{"email": "ada@example.com", "password": "' + b"hunter2" * 1000 + b'"}',
    ],
)
async def test_a_validation_error_never_echoes_what_was_sent(
    client: httpx.AsyncClient, content: bytes
) -> None:
    response = await client.post(
        "/api/auth/signin", content=content, headers={"Content-Type": "application/json"}
    )
    assert (response.status_code, response.json()["error"]["code"]) == (422, "validation_failed")
    assert "hunter2" not in response.text


@pytest.mark.parametrize("content_type", ["application/x-www-form-urlencoded", "text/plain"])
async def test_a_body_that_is_not_json_is_a_validation_error(
    client: httpx.AsyncClient, content_type: str
) -> None:
    response = await client.post(
        "/api/auth/signin",
        content=b"email=ada@example.com&password=hunter2hunter2",
        headers={"Content-Type": content_type},
    )
    assert (response.status_code, response.json()["error"]["code"]) == (422, "validation_failed")
    assert "hunter2" not in response.text


async def test_a_database_failure_while_signing_in_leaks_nothing(settings: Settings) -> None:
    unreachable = SecretStr("postgresql+psycopg://nobody:wrong@127.0.0.1:1/none")
    app = create_app(settings.model_copy(update={"database_url": unreachable}))
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await sign_in(client)
    await app.state.database.dispose()
    assert (response.status_code, response.json()["error"]["code"]) == (500, "internal_error")
    for leaked in ("nobody", "127.0.0.1", "psycopg", "Traceback"):
        assert leaked not in response.text


async def sign_in_with_json_text(
    client: httpx.AsyncClient, email: str, password: str
) -> httpx.Response:
    """The two values are JSON string contents, so escapes like \\ud800 reach the server as sent
    (httpx's json= can't encode a lone surrogate)."""
    body = f'{{"email": "{email}", "password": "{password}"}}'
    return await client.post(
        "/api/auth/signin", content=body.encode(), headers={"Content-Type": "application/json"}
    )


@pytest.mark.parametrize(
    ("email", "password"),
    [("\\ud800@example.com", "correct horse battery"), ("ada@example.com", "correct\\ud800horse")],
)
async def test_a_lone_surrogate_is_refused_by_the_schema(
    client: httpx.AsyncClient, email: str, password: str
) -> None:
    response = await sign_in_with_json_text(client, email, password)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "validation_failed")


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("\\u0000@example.com", "correct horse battery"),
        ("ada@example.com\\u0000", "correct horse battery"),
        ("ada@example.com", "correct\\u0000horse battery"),
    ],
)
async def test_a_nul_in_the_email_or_password_is_just_a_wrong_password(
    client: httpx.AsyncClient, email: str, password: str
) -> None:
    response = await sign_in_with_json_text(client, email, password)
    assert (response.status_code, response.json()["error"]["code"]) == (401, "invalid_credentials")


async def test_a_mismatched_csrf_header_is_refused_and_the_token_survives(
    client: httpx.AsyncClient,
) -> None:
    await sign_in(client)
    refused = await client.post("/api/auth/signout", headers={"X-CSRF-Token": "not-the-cookie"})
    assert (refused.status_code, refused.json()["error"]["code"]) == (403, "csrf_failed")
    assert (await client.get("/api/auth/session")).status_code == 200


async def test_signing_out_with_no_csrf_cookie_is_refused(client: httpx.AsyncClient) -> None:
    await sign_in(client)
    client.cookies.delete("fource_csrf")
    for header in ({"X-CSRF-Token": "anything"}, {"X-CSRF-Token": ""}, {}):
        refused = await client.post("/api/auth/signout", headers=header)
        assert (refused.status_code, refused.json()["error"]["code"]) == (403, "csrf_failed")
    assert (await client.get("/api/auth/session")).status_code == 200


async def test_a_non_ascii_csrf_header_is_refused_not_a_crash(client: httpx.AsyncClient) -> None:
    await sign_in(client)
    refused = await client.post("/api/auth/signout", headers=[(b"x-csrf-token", b"caf\xe9")])
    assert (refused.status_code, refused.json()["error"]["code"]) == (403, "csrf_failed")


@pytest.mark.parametrize(
    "token",
    [b"", b"x", b"a.b.c", b"caf\xe9", b"\xff.\xfe.\xfd", b"x" * 100_000],
    ids=["empty", "one-char", "three-parts", "non-ascii", "invalid-utf8", "100k"],
)
async def test_a_garbage_bearer_token_is_not_authenticated(
    client: httpx.AsyncClient, token: bytes
) -> None:
    response = await client.get(
        "/api/auth/session", headers=[(b"authorization", b"Bearer " + token)]
    )
    assert (response.status_code, response.json()["error"]["code"]) == (401, "not_authenticated")


async def test_a_garbage_token_cookie_is_not_authenticated(client: httpx.AsyncClient) -> None:
    client.cookies.set("fource_token", "garbage")
    response = await client.get("/api/auth/session")
    assert (response.status_code, response.json()["error"]["code"]) == (401, "not_authenticated")


async def test_signing_out_clears_both_cookies(client: httpx.AsyncClient) -> None:
    await sign_in(client)
    header = {"X-CSRF-Token": client.cookies["fource_csrf"]}
    response = await client.post("/api/auth/signout", headers=header)
    cleared = response.headers.get_list("set-cookie")
    for name in ("fource_token", "fource_csrf"):
        assert any(c.startswith(f"{name}=") and "Max-Age=0" in c for c in cleared)


async def test_the_cookies_are_secure_only_over_https(client: httpx.AsyncClient) -> None:
    plain = (await sign_in(client)).headers.get_list("set-cookie")
    assert not any("Secure" in cookie for cookie in plain)
    client.base_url = httpx.URL("https://test")
    secure = (await sign_in(client)).headers.get_list("set-cookie")
    assert len(secure) == 2 and all("Secure" in cookie for cookie in secure)


async def test_the_factory_reads_its_settings_from_the_environment(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FOURCE_SECRET_KEY", "k" * 40)
    monkeypatch.setenv("FOURCE_ORG", "elsewhere")
    app = app_factory()
    await app.state.database.dispose()
    assert app.state.settings.org == "elsewhere"
    assert app.state.settings.secret_key.get_secret_value() == "k" * 40


async def test_signing_in_before_the_database_is_set_up_says_so(settings: Settings) -> None:
    app = create_app(settings.model_copy(update={"org": "nowhere"}))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await sign_in(client)
    await app.state.database.dispose()
    assert (response.status_code, response.json()["error"]["code"]) == (503, "setup_incomplete")


def _schema_ref(contract: dict[str, Any], path: str, method: str, status: str) -> str:
    response = contract["paths"][path][method]["responses"][status]
    ref: str = response["content"]["application/json"]["schema"]["$ref"]
    return ref


async def test_the_contract_declares_the_error_envelope_not_fastapis_default(
    settings: Settings,
) -> None:
    app = create_app(settings)
    contract = app.openapi()
    await app.state.database.dispose()
    declared = {
        ("/api/auth/signin", "post"): ["401", "422", "423", "503"],
        ("/api/auth/session", "get"): ["401"],
        ("/api/auth/signout", "post"): ["401", "403"],
    }
    for (path, method), statuses in declared.items():
        for status in statuses:
            assert _schema_ref(contract, path, method, status) == "#/components/schemas/ErrorOut"
    assert "HTTPValidationError" not in json.dumps(contract)
    error = contract["components"]["schemas"]["ErrorOut"]["properties"]["error"]
    assert error["$ref"].endswith("/ErrorBody")
    assert set(contract["components"]["schemas"]["ErrorBody"]["properties"]) == {"code", "message"}


async def test_an_unknown_path_and_a_wrong_method_use_the_envelope(
    client: httpx.AsyncClient,
) -> None:
    missing = await client.get("/api/nope")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"
    wrong = await client.post("/api/health")
    assert wrong.status_code == 405
    assert wrong.json()["error"]["code"] == "method_not_allowed"
    assert wrong.headers["allow"]  # Starlette's own headers survive


async def test_another_starlette_error_gets_a_generic_code(settings: Settings) -> None:
    app = create_app(settings)

    async def teapot() -> None:
        raise StarletteHTTPException(status_code=418, detail="short and stout")

    app.add_api_route("/api/teapot", teapot)
    response = await get_from(app, "/api/teapot")
    assert response.status_code == 418
    assert response.json()["error"]["code"] == "http_error"


async def test_signing_in_to_an_unmigrated_database_says_so(
    tmp_path: Path, settings: Settings
) -> None:
    bare = f"sqlite+aiosqlite:///{(tmp_path / 'bare.db').as_posix()}"
    app = create_app(settings.model_copy(update={"database_url": SecretStr(bare)}))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await sign_in(client)
    await app.state.database.dispose()
    assert (response.status_code, response.json()["error"]["code"]) == (503, "setup_incomplete")


async def test_a_second_sign_out_with_the_same_credentials_is_not_authenticated(
    client: httpx.AsyncClient,
) -> None:
    await sign_in(client)
    cookies = dict(client.cookies)
    header = {"X-CSRF-Token": cookies["fource_csrf"]}
    assert (await client.post("/api/auth/signout", headers=header)).status_code == 204
    client.cookies.update(cookies)  # the browser that kept the old cookies
    again = await client.post("/api/auth/signout", headers=header)
    assert (again.status_code, again.json()["error"]["code"]) == (401, "not_authenticated")


async def test_a_failed_sign_in_through_the_api_is_recorded(
    client: httpx.AsyncClient, settings: Settings
) -> None:
    assert (await sign_in(client, "wrong horse battery")).status_code == 401
    database = Database(settings.database_url.get_secret_value())
    try:
        org_id = await database.org_id(settings.org)
        assert org_id is not None
        async with database.org_session(org_id) as session:
            types = [entry.type async for entry in read_entries(session)]
    finally:
        await database.dispose()
    assert types == [EntryType.USER_CREATE, EntryType.SIGNIN_FAILURE]
