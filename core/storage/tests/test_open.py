import os
import subprocess
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from pydantic import SecretStr

from fource.common import Settings
from fource.db import Database
from fource.storage import FileTooLarge, S3Blobs, open_storage

pytestmark = pytest.mark.anyio
SECRET = SecretStr("s" * 40)


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No .env file and no FOURCE_* variable from the developer's shell reach these settings,
    so none of them can pick a store or point one at a real MinIO."""
    monkeypatch.chdir(tmp_path)
    for name in [n for n in os.environ if n.startswith("FOURCE_")]:
        monkeypatch.delenv(name)


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def test_local_files_live_under_the_data_folder_with_the_size_limit(
    orgs: tuple[Database, uuid.UUID, uuid.UUID], tmp_path: Path
) -> None:
    database, first, _ = orgs
    settings = Settings(
        secret_key=SECRET, storage="local", data_dir=tmp_path, storage_max_file_mb=1
    )
    storage = open_storage(settings)
    assert storage.blobs.backend == "local" and await storage.ping()
    assert (tmp_path / "files").is_dir()
    with pytest.raises(FileTooLarge, match="1 MiB"):
        async with database.org_session(first) as session:
            chunks = source(b"x" * 1024 * 1024, b"y")
            await storage.put(session, chunks, name="a", content_type="text/plain", actor="system")
    await storage.close()


async def test_s3_storage_uses_the_bucket_and_needs_no_network_to_open() -> None:
    settings = Settings(
        secret_key=SECRET,
        storage="s3",
        s3_endpoint="http://127.0.0.1:9",
        s3_access_key="key",
        s3_secret_key=SecretStr("s3-secret"),
        s3_bucket="files-test",
    )
    storage = open_storage(settings)
    assert storage.blobs.backend == "s3" and isinstance(storage.blobs, S3Blobs)
    probe = vars(storage.blobs.probe.meta.config)  # health's check: one try, 2 s and 2 s
    assert (probe["connect_timeout"], probe["read_timeout"], probe["retries"]) == (
        2,
        2,
        {"mode": "standard", "total_max_attempts": 1},
    )
    await storage.close()


def test_local_storage_never_imports_boto3(tmp_path: Path) -> None:
    script = (
        "import sys\n"
        "from pydantic import SecretStr\n"
        "from fource.common import Settings\n"
        "from fource.storage import open_storage\n"
        "open_storage(Settings(secret_key=SecretStr('s' * 40), storage='local'))\n"
        "assert 'boto3' not in sys.modules and 'botocore' not in sys.modules\n"
    )
    clean = {name: value for name, value in os.environ.items() if not name.startswith("FOURCE_")}
    subprocess.run([sys.executable, "-c", script], check=True, cwd=tmp_path, env=clean)
