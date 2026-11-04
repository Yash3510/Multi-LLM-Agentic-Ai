import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

from fource.db import Database
from fource.identity import Role, create_user
from fource.server.deps import TOKEN_COOKIE
from fource.server.loops import asyncio_loop_factory

EMAIL = "ada@example.com"
PASSWORD = "correct horse battery"


async def _create_user(url: str) -> None:
    database = Database(url)
    try:
        org_id = await database.org_id("default")
        assert org_id is not None
        async with database.org_session(org_id) as session:
            await create_user(session, email=EMAIL, password=PASSWORD, roles=[Role.ADMIN])
    finally:
        await database.dispose()


def test_the_server_command_runs_and_signs_in(tmp_path: Path) -> None:
    name = "fource-server.exe" if sys.platform == "win32" else "fource-server"
    script = Path(sys.executable).parent / name
    assert script.exists(), f"{script} is missing: is the server package installed?"

    url = "sqlite+aiosqlite:///" + (tmp_path / "smoke.db").as_posix()
    # cwd is tmp_path below, so no developer .env is read
    env = {k: v for k, v in os.environ.items() if not k.startswith("FOURCE_")}
    env |= {"FOURCE_SECRET_KEY": "k" * 40, "FOURCE_DATABASE_URL": url}

    migrated = subprocess.run(
        [str(script), "migrate"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert migrated.returncode == 0, f"{migrated.stdout}\n{migrated.stderr}"

    asyncio.run(_create_user(url), loop_factory=asyncio_loop_factory())

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    log_path = tmp_path / "server.log"

    with log_path.open("w") as log:
        proc = subprocess.Popen(
            [str(script), "serve", "--host", "127.0.0.1", "--port", str(port)],
            env=env,
            cwd=tmp_path,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 60
            while True:
                try:
                    if httpx.get(f"{base}/api/health", timeout=2).status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                assert proc.poll() is None and time.monotonic() < deadline, (
                    f"the server did not come up:\n{log_path.read_text()}"
                )
                time.sleep(0.25)

            signed_in = httpx.post(
                f"{base}/api/auth/signin", json={"email": EMAIL, "password": PASSWORD}, timeout=10
            )
            assert signed_in.status_code == 200, signed_in.text
            token = signed_in.cookies.get(TOKEN_COOKIE)
            assert token, f"no {TOKEN_COOKIE} cookie was set"

            session = httpx.get(
                f"{base}/api/auth/session",
                headers={"Cookie": f"{TOKEN_COOKIE}={token}"},
                timeout=10,
            )
            assert session.status_code == 200, session.text
            assert EMAIL in session.text
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
