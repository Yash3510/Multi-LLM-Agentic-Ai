from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from fource.server.deps import database_of, live_of, storage_of

router = APIRouter(prefix="/api", tags=["health"])


class Health(BaseModel):
    status: str
    database: str
    redis: str
    storage: str


@router.get("/health", response_model=Health, responses={503: {"model": Health}})
async def health(request: Request) -> JSONResponse:
    """503 when the database, a configured Redis or the file store can't be reached: without
    Redis the server refuses new sign-ins (ADR-0026), and without the file store no file can
    be kept or read (ADR-0044). "off" means no Redis is configured (development)."""
    database = "ok" if await database_of(request).ping() else "unavailable"
    live = live_of(request)
    if live.backend == "memory":
        redis = "off"
    else:
        redis = "ok" if await live.ping() else "unavailable"
    storage = "ok" if await storage_of(request).ping() else "unavailable"
    ok = database == "ok" and redis != "unavailable" and storage == "ok"
    body = {
        "status": "ok" if ok else "unavailable",
        "database": database,
        "redis": redis,
        "storage": storage,
    }
    return JSONResponse(body, status_code=200 if ok else 503)
