from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fource.common import FourceError


class CsrfFailed(FourceError):
    code = "csrf_failed"
    status = 403


class SetupIncomplete(FourceError):
    code = "setup_incomplete"
    status = 503


def error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


async def _known(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, FourceError)
    return error_response(error.code, error.message, error.status)


async def _invalid(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)
    problems = error.errors()
    first: dict[str, Any] = problems[0] if problems else {}  # FastAPI types each as Any
    field = ".".join(str(part) for part in first.get("loc", ())[1:]) or "request"
    return error_response("validation_failed", f"{field}: {first.get('msg', 'invalid')}", 422)


async def _unexpected(request: Request, error: Exception) -> JSONResponse:
    """Nothing about the failure reaches the client; the server still logs it, because
    Starlette raises the error again after sending this response."""
    return error_response("internal_error", "Something went wrong on the server.", 500)


def install_error_handlers(app: FastAPI) -> None:
    """Every error leaves as {"error": {"code", "message"}} (docs/architecture/api.md)."""
    app.add_exception_handler(FourceError, _known)
    app.add_exception_handler(RequestValidationError, _invalid)
    app.add_exception_handler(Exception, _unexpected)
