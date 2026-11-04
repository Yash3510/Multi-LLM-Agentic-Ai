from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from fource.common import FourceError


class CsrfFailed(FourceError):
    code = "csrf_failed"
    status = 403


class SetupIncomplete(FourceError):
    code = "setup_incomplete"
    status = 503


class RateLimited(FourceError):
    """Too many attempts from one client address; the answer says when to try again."""

    code = "rate_limited"
    status = 429

    def __init__(self, message: str, *, retry_after: int) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitUnavailable(FourceError):
    """The rate limit can't be checked (Redis is down), so the attempt is refused (ADR-0026)."""

    code = "rate_limit_unavailable"
    status = 503


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    """The shape of every error, for the OpenAPI document (docs/architecture/api.md)."""

    error: ErrorBody


_RETRY_AFTER = {
    "Retry-After": {
        "description": "Seconds to wait before trying again.",
        "schema": {"type": "integer", "minimum": 1},
    }
}


def declared(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """The `responses=` of a route that can answer these error statuses. A 429 (RateLimited)
    always carries Retry-After."""
    return {
        status: {"model": ErrorOut, "description": "Error"}
        | ({"headers": _RETRY_AFTER} if status == 429 else {})
        for status in statuses
    }


def error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


async def _known(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, FourceError)
    response = error_response(error.code, error.message, error.status)
    if isinstance(error, RateLimited):
        response.headers["Retry-After"] = str(error.retry_after)
    return response


async def _invalid(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    problems = error.errors()
    first: dict[str, Any] = problems[0] if problems else {}  # FastAPI types each as Any
    field = ".".join(str(part) for part in first.get("loc", ())[1:]) or "request"
    return error_response("validation_failed", f"{field}: {first.get('msg', 'invalid')}", 422)


_HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


async def _http(request: Request, error: Exception) -> JSONResponse:
    """Starlette's own answers: an unknown path, a wrong method."""
    assert isinstance(error, StarletteHTTPException)
    code = _HTTP_CODES.get(error.status_code, "http_error")
    response = error_response(code, str(error.detail), error.status_code)
    response.headers.update(error.headers or {})  # such as Allow on a 405
    return response


async def _unexpected(request: Request, error: Exception) -> JSONResponse:
    """Nothing about the failure reaches the client; the server still logs it, because
    Starlette raises the error again after sending this response."""
    return error_response("internal_error", "Something went wrong on the server.", 500)


def install_error_handlers(app: FastAPI) -> None:
    """Every error leaves as {"error": {"code", "message"}} (docs/architecture/api.md)."""
    app.add_exception_handler(FourceError, _known)
    app.add_exception_handler(RequestValidationError, _invalid)
    app.add_exception_handler(StarletteHTTPException, _http)
    app.add_exception_handler(Exception, _unexpected)
