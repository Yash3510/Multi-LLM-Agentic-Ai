import os
import stat
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import pytest

from fource.storage import BlobKey, BlobMissing, LocalBlobs, StorageUnavailable

pytestmark = pytest.mark.anyio
ORG = uuid.UUID("0190a0b1-0000-7000-8000-000000000001")


async def source(*parts: bytes) -> AsyncIterator[bytes]:
    for part in parts:
        yield part


async def slow_source() -> AsyncIterator[bytes]:
    yield b"first part"
    await anyio.sleep(30)
    yield b"never sent"


def leftovers(root: Path) -> list[str]:
    return sorted(path.name for path in root.rglob("*") if path.is_file())


async def test_a_failing_source_leaves_no_part_file(tmp_path: Path) -> None:
    blobs = LocalBlobs(tmp_path / "files")

    async def failing() -> AsyncIterator[bytes]:
        yield b"half"
        raise ValueError("broke off")

    with pytest.raises(ValueError):
        await blobs.write(BlobKey(ORG, uuid.uuid4()), failing())
    assert leftovers(tmp_path / "files") == []


async def test_a_cancelled_write_leaves_no_part_file(tmp_path: Path) -> None:
    blobs = LocalBlobs(tmp_path / "files")
    at = BlobKey(ORG, uuid.uuid4())
    with anyio.move_on_after(1):  # the source never finishes; a slow machine only waits longer
        await blobs.write(at, slow_source())
    assert leftovers(tmp_path / "files") == []
    with pytest.raises(BlobMissing):
        async with blobs.read(at):
            pass


async def test_a_written_file_sits_under_its_organisation_and_id(tmp_path: Path) -> None:
    blobs = LocalBlobs(tmp_path / "files")
    at = BlobKey(ORG, uuid.uuid4())
    await blobs.write(at, source(b"hello"))
    assert (tmp_path / "files" / at.path).read_bytes() == b"hello"
    assert leftovers(tmp_path / "files") == [at.file.hex]  # no part file stays behind
    if os.name == "posix":  # owner-only, whatever the umask lets through for others
        assert stat.S_IMODE(os.stat(tmp_path / "files").st_mode) == 0o700
        assert stat.S_IMODE(os.stat(tmp_path / "files" / at.path).st_mode) == 0o600


async def test_an_organisation_folder_that_is_a_link_is_refused(tmp_path: Path) -> None:
    if os.name == "posix":  # creating links on Windows needs a privilege; POSIX shows it
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (tmp_path / "files").mkdir()
        (tmp_path / "files" / ORG.hex).symlink_to(elsewhere, target_is_directory=True)
        blobs = LocalBlobs(tmp_path / "files")
        with pytest.raises(StorageUnavailable, match="link"):
            await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"x"))
        with pytest.raises(StorageUnavailable, match="link"):
            async with blobs.read(BlobKey(ORG, uuid.uuid4())):
                pass
        assert list(elsewhere.iterdir()) == []


async def test_a_file_that_is_a_link_is_not_followed(tmp_path: Path) -> None:
    if os.name == "posix":
        blobs = LocalBlobs(tmp_path / "files")
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"mine"))
        secret = tmp_path / "secret.txt"
        secret.write_bytes(b"not 4CE's")
        target = tmp_path / "files" / at.path
        target.unlink()
        target.symlink_to(secret)
        with pytest.raises(StorageUnavailable, match="link"):
            async with blobs.read(at):
                pass


async def test_ping_fails_when_the_root_cannot_be_a_folder(tmp_path: Path) -> None:
    (tmp_path / "taken").write_bytes(b"a file where the folder should be")
    assert not await LocalBlobs(tmp_path / "taken").ping()
    assert await LocalBlobs(tmp_path / "new" / "files").ping()
