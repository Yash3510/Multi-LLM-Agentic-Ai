"""The fource-server command: serve, worker, migrate, create-user, ledger."""

import argparse
import asyncio
import getpass
from pathlib import Path

import uvicorn
from sqlalchemy.exc import OperationalError

from fource.common import FourceError, Settings
from fource.db import Database
from fource.identity import Role, create_user
from fource.server import ledger_commands
from fource.server.loops import asyncio_loop_factory, uvicorn_loop
from fource.server.migrate import migration_url, upgrade
from fource.server.worker import run_worker


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fource-server", description="Run and manage 4CE.")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="run the API server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="restart when code changes")
    work = commands.add_parser("worker", help="run queued jobs until stopped")
    work.add_argument("--once", action="store_true", help="run the jobs that are due, then exit")
    commands.add_parser("migrate", help="bring the database schema up to date")
    create = commands.add_parser("create-user", help="add a user; asks for the password")
    create.add_argument("email")
    create.add_argument(
        "--role", action="append", required=True, choices=[role.value for role in Role]
    )
    create.add_argument("--name", default="")
    ledger = commands.add_parser("ledger", help="sign and check the evidence ledger")
    actions = ledger.add_subparsers(dest="action", required=True)
    actions.add_parser("keygen", help="create the installation's signing key")
    sign = actions.add_parser("checkpoint", help="sign the chain head and save the checkpoint")
    sign.add_argument("--org", help="organisation slug (default: FOURCE_ORG)")
    sign.add_argument("--out", type=Path, help="folder for the checkpoint file")
    check = actions.add_parser("verify", help="check the chain and its checkpoints")
    check.add_argument("--org", help="organisation slug (default: FOURCE_ORG)")
    check.add_argument("--public-key", type=Path, help="the installation's public key file")
    check.add_argument("--checkpoints", type=Path, help="folder of checkpoint files")
    return parser


def _ledger(settings: Settings, args: argparse.Namespace) -> int:
    if args.action == "keygen":
        return ledger_commands.keygen(settings)
    slug: str = args.org or settings.org
    if args.action == "checkpoint":
        work = ledger_commands.make_checkpoint(settings, slug, args.out)
    else:
        work = ledger_commands.verify(settings, slug, args.public_key, args.checkpoints)
    return asyncio.run(work, loop_factory=asyncio_loop_factory())


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
    if args.command == "worker":
        try:
            return asyncio.run(
                run_worker(settings, once=args.once), loop_factory=asyncio_loop_factory()
            )
        except (KeyboardInterrupt, asyncio.CancelledError):  # a second signal, or Windows
            print("Stopped.")
            return 130
    if args.command == "ledger":
        return _ledger(settings, args)
    if args.command == "migrate":
        upgrade(migration_url(settings))
        print("The database is up to date.")
        return 0
    return asyncio.run(
        _create_user(settings, args.email, args.role, args.name),
        loop_factory=asyncio_loop_factory(),
    )
