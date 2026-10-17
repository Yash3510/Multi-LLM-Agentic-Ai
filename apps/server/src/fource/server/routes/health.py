from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fource.server.deps import database_of

router = APIRouter(prefix="/api", tags=["health"])


class Health(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=Health, responses={503: {"model": Health}})
async def health(request: Request) -> JSONResponse:
    ok = await database_of(request).ping()
    state = "ok" if ok else "unavailable"
    return JSONResponse({"status": state, "database": state}, status_code=200 if ok else 503)
