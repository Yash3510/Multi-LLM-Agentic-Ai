"""The fource-server command: serve, migrate, create-user."""

import argparse
import asyncio
import getpass

import uvicorn
from sqlalchemy.exc import OperationalError

from fource.common import FourceError, Settings
from fource.db import Database
from fource.identity import Role, create_user
from fource.server.loops import asyncio_loop_factory, uvicorn_loop
from fource.server.migrate import migration_url, upgrade


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fource-server", description="Run and manage 4CE.")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="run the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="restart when code changes")
    commands.add_parser("migrate", help="bring the database schema up to date")
    create = commands.add_parser("create-user", help="add a user; asks for the password")
    create.add_argument("email")
    create.add_argument(
        "--role", action="append", required=True, choices=[role.value for role in Role]
    )
    create.add_argument("--name", default="")
    return parser


async def _create_user(settings: Settings, email: str, roles: list[str], name: str) -> int:
    first = getpass.getpass("Password: ")
    if getpass.getpass("Again: ") != first:
        print("The passwords don't match; nothing was created.")
        return 1
    database = Database(settings.database_url.get_secret_value())
    try:
        org_id = await database.org_id(settings.org)
        if org_id is None:
            print("The database isn't set up yet: run `just migrate` first.")
            return 1
        async with database.org_session(org_id) as session:
            user = await create_user(
                session, email=email, password=first, roles=roles, display_name=name
            )
            print(f"Created {user.email} ({', '.join(user.roles)}).")
        return 0
    except FourceError as error:
        print(error.message)
        return 1
    except OperationalError:
        print("The database isn't set up yet: run `just migrate` first.")
        return 1
    finally:
        await database.dispose()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings()
    if args.command == "serve":
        uvicorn.run(
            "fource.server.main:app_factory",
            factory=True,
            host=args.host,
            port=args.port,
            reload=args.reload,
            loop=uvicorn_loop(),
        )
        return 0
    if args.command == "migrate":
        upgrade(migration_url(settings))
        print("The database is up to date.")
        return 0
    return asyncio.run(
        _create_user(settings, args.email, args.role, args.name),
        loop_factory=asyncio_loop_factory(),
    )
