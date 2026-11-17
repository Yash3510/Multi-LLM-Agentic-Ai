import os
import secrets
import stat
import sys
import threading
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import pytest

from fource.storage import BlobKey, BlobMissing, LocalBlobs, StorageUnavailable

if sys.platform != "win32":  # Windows has neither module
    import grp
    import pwd

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


async def test_a_file_is_synced_before_it_is_renamed_into_place(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []
    real_fsync = os.fsync
    real_replace = os.replace

    def fsync(descriptor: int) -> None:
        events.append("fsync")
        real_fsync(descriptor)

    def replace(source_path: Path, target_path: Path) -> None:
        events.append("replace")
        real_replace(source_path, target_path)

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "replace", replace)
    await LocalBlobs(tmp_path / "files").write(BlobKey(ORG, uuid.uuid4()), source(b"x"))
    assert events[:2] == ["fsync", "replace"]  # the folder is synced after, on POSIX


async def test_a_file_that_cannot_be_synced_is_not_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_fsync(descriptor: int) -> None:
        raise OSError(5, "Input/output error")

    monkeypatch.setattr(os, "fsync", failing_fsync)
    blobs = LocalBlobs(tmp_path / "files")
    at = BlobKey(ORG, uuid.uuid4())
    with pytest.raises(StorageUnavailable):
        await blobs.write(at, source(b"x"))
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
        assert stat.S_IMODE(os.stat(tmp_path / "files" / ORG.hex).st_mode) == 0o700
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
        at = BlobKey(ORG, uuid.uuid4())
        (elsewhere / at.file.hex).write_bytes(b"not 4CE's")
        with pytest.raises(StorageUnavailable, match="link"):
            await blobs.delete(at)
        assert (elsewhere / at.file.hex).read_bytes() == b"not 4CE's"  # delete did not follow it


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


async def test_a_folder_others_may_write_is_refused(tmp_path: Path) -> None:
    if sys.platform != "win32":  # Windows keeps its own permissions (ADR-0044, point 7)
        blobs = LocalBlobs(tmp_path / "files")
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"x"))
        for folder in (tmp_path / "files" / ORG.hex, tmp_path / "files"):
            folder.chmod(0o707)  # every account may now add, swap or plant entries
            with pytest.raises(StorageUnavailable, match="another account"):
                async with blobs.read(at):
                    pass
            with pytest.raises(StorageUnavailable, match="another account"):
                await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"y"))
            with pytest.raises(StorageUnavailable, match="another account"):
                await blobs.delete(at)
            assert (tmp_path / "files" / at.path).read_bytes() == b"x"  # nothing was removed
            folder.chmod(0o700)
        async with blobs.read(at) as chunks:
            assert b"".join([chunk async for chunk in chunks]) == b"x"


async def test_group_write_passes_only_for_the_owners_private_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":
        blobs = LocalBlobs(tmp_path / "files")
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"x"))
        (tmp_path / "files").chmod(0o770)
        owner = pwd.getpwuid(os.geteuid()).pw_name
        group = grp.struct_group(("shared", "x", os.getegid(), [owner, "someone-else"]))

        def shared_group(gid: int) -> grp.struct_group:
            return group

        monkeypatch.setattr(grp, "getgrgid", shared_group)
        with pytest.raises(StorageUnavailable, match="another account"):
            async with blobs.read(at):
                pass
        private = grp.struct_group((owner, "x", os.getegid(), []))

        def private_group(gid: int) -> grp.struct_group:
            return private

        monkeypatch.setattr(grp, "getgrgid", private_group)
        async with blobs.read(at) as chunks:  # a umask of 002 with a private group is fine
            assert b"".join([chunk async for chunk in chunks]) == b"x"


async def test_an_account_with_the_group_as_its_primary_group_counts_as_another(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":
        blobs = LocalBlobs(tmp_path / "files")
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"x"))
        (tmp_path / "files").chmod(0o770)
        info = os.stat(tmp_path / "files")
        owner = pwd.getpwuid(os.geteuid()).pw_name
        private = grp.struct_group((owner, "x", info.st_gid, []))  # no supplementary members

        def private_group(gid: int) -> grp.struct_group:
            return private

        monkeypatch.setattr(grp, "getgrgid", private_group)
        async with blobs.read(at) as chunks:  # nobody else is in the group: fine
            assert b"".join([chunk async for chunk in chunks]) == b"x"
        accounts = pwd.getpwall()
        service = pwd.struct_passwd(
            ("svc", "x", os.geteuid() + 4242, info.st_gid, "", "/nonexistent", "/bin/false")
        )

        def with_service_account() -> list[pwd.struct_passwd]:
            return [*accounts, service]  # it is not in gr_mem, yet the group is its own

        monkeypatch.setattr(pwd, "getpwall", with_service_account)
        with pytest.raises(StorageUnavailable, match="another account"):
            async with blobs.read(at):
                pass


async def test_a_folder_above_the_store_needs_the_sticky_bit_if_others_may_write(
    tmp_path: Path,
) -> None:
    if sys.platform != "win32":
        shared = tmp_path / "shared"
        shared.mkdir()
        shared.chmod(0o777)  # anyone could move the store away and put their own in its place
        blobs = LocalBlobs(shared / "files")
        with pytest.raises(StorageUnavailable, match="another account"):
            await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"x"))
        assert not await blobs.ping()
        shared.chmod(0o1777)  # sticky, as /tmp: only an entry's owner may move or remove it
        await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"x"))
        assert await blobs.ping()


async def test_a_folder_another_account_owns_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if sys.platform != "win32":
        blobs = LocalBlobs(tmp_path / "files")
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"x"))
        me = os.geteuid()
        monkeypatch.setattr(os, "geteuid", lambda: me + 4242)  # 4CE now runs as someone else
        with pytest.raises(StorageUnavailable, match="another account"):
            async with blobs.read(at):
                pass


@pytest.mark.parametrize("which", ["organisation", "store", "above"])
async def test_each_folder_owner_check_refuses_on_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, which: str
) -> None:
    if sys.platform != "win32":
        root = Path(os.path.realpath(tmp_path / "files"))
        blobs = LocalBlobs(root)
        at = BlobKey(ORG, uuid.uuid4())
        await blobs.write(at, source(b"x"))
        foreign = {"organisation": root / ORG.hex, "store": root, "above": root.parent}[which]
        real_lstat = os.lstat

        def lstat(path: Path) -> os.stat_result:
            info = real_lstat(path)
            if Path(path) != foreign:
                return info
            fields = list(info)
            fields[stat.ST_UID] = os.geteuid() + 4242  # only this folder is another account's
            return os.stat_result(fields)

        monkeypatch.setattr(os, "lstat", lstat)
        with pytest.raises(StorageUnavailable, match="another account"):
            async with blobs.read(at):
                pass


async def test_an_os_error_never_puts_a_path_into_a_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blobs = LocalBlobs(tmp_path / "files")
    at = BlobKey(ORG, uuid.uuid4())
    await blobs.write(at, source(b"x"))
    real_open = os.open

    def denied(path: Path, flags: int, mode: int = 0o777) -> int:
        if Path(path).is_relative_to(tmp_path):  # an error that names the file, as the OS does
            raise OSError(13, "Permission denied", str(path))
        return real_open(path, flags, mode)

    monkeypatch.setattr(os, "open", denied)
    with pytest.raises(StorageUnavailable) as read_error:
        async with blobs.read(at):
            pass
    with pytest.raises(StorageUnavailable) as write_error:
        await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"y"))
    for error in (read_error.value, write_error.value):
        assert "Permission denied" in str(error)
        assert str(tmp_path) not in str(error)
        assert ORG.hex not in str(error)


async def test_a_part_file_that_already_exists_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blobs = LocalBlobs(tmp_path / "files")
    await blobs.write(BlobKey(ORG, uuid.uuid4()), source(b"x"))  # makes the organisation folder
    at = BlobKey(ORG, uuid.uuid4())
    planted = tmp_path / "files" / ORG.hex / f".{at.file.hex}.{'0' * 16}.part"
    planted.write_bytes(b"someone else's")

    def known_name(nbytes: int | None = None) -> str:
        return "0" * 16

    monkeypatch.setattr(secrets, "token_hex", known_name)  # the part file's name is now known
    with pytest.raises(StorageUnavailable):
        await blobs.write(at, source(b"mine"))
    assert planted.read_bytes() == b"someone else's"


async def test_ping_does_its_file_work_off_the_event_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loop_thread = threading.get_ident()
    calls: list[tuple[str, int]] = []
    real_is_dir = Path.is_dir
    real_access = os.access

    def is_dir(self: Path) -> bool:
        calls.append(("is_dir", threading.get_ident()))
        return real_is_dir(self)

    def access(path: Path, mode: int) -> bool:
        calls.append(("access", threading.get_ident()))
        return real_access(path, mode)

    monkeypatch.setattr(Path, "is_dir", is_dir)
    monkeypatch.setattr(os, "access", access)
    assert await LocalBlobs(tmp_path / "files").ping()
    assert {name for name, _ in calls} == {"is_dir", "access"}
    assert all(thread != loop_thread for _, thread in calls)  # a slow disk can't stall the loop


async def test_a_new_organisation_folder_is_synced_into_the_store_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name == "posix":  # Windows can't open a folder to sync it
        root = Path(os.path.realpath(tmp_path / "files"))
        opened: list[Path] = []
        real_open = os.open

        def opening(path: Path, flags: int, mode: int = 0o777) -> int:
            opened.append(Path(path))
            return real_open(path, flags, mode)

        monkeypatch.setattr(os, "open", opening)
        await LocalBlobs(root).write(BlobKey(ORG, uuid.uuid4()), source(b"x"))
        # The new folder's entry lives in the store folder; without this sync a power cut after
        # the write was reported done could lose the folder and the file in it.
        assert root in opened
        assert root / ORG.hex in opened
