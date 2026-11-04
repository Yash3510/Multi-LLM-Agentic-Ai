"""Runs every migration with the async engine, on SQLite or PostgreSQL."""

import asyncio

from alembic import context
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from fource.db import Base, Org
from fource.identity import RevokedToken, User
from fource.jobs import Job
from fource.ledger import LedgerEntry, LedgerHead
from fource.server.loops import asyncio_loop_factory

# Each model imported here puts its table on Base.metadata.
MODELS = (Org, User, RevokedToken, LedgerEntry, LedgerHead, Job)


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


async def _main() -> None:
    engine = create_async_engine(context.config.get_main_option("sqlalchemy.url") or "")
    async with engine.connect() as connection:
        await connection.run_sync(_run)
        await connection.commit()
    await engine.dispose()


asyncio.run(_main(), loop_factory=asyncio_loop_factory())
