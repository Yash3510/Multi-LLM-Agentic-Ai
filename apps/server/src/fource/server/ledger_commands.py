"""The `fource-server ledger` commands: keygen, checkpoint and verify (ADR-0014).

Signing is for people: nothing in CI or the tests signs with a real installation key.
"""

import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy.exc import OperationalError

from fource.common import FourceError, Settings
from fource.db import Database
from fource.ledger import (
    Checkpoint,
    UnusableKey,
    Verification,
    checkpoint,
    load_private_key,
    load_public_key,
    public_key_path,
    verify_ledger,
    write_key_pair,
)

VERIFIED, FAILED, INCOMPLETE = 0, 1, 2
_NOT_SET_UP = "The database isn't set up yet: run `just migrate` first."


def key_file(settings: Settings) -> Path:
    return settings.ledger_key_file or settings.data_dir / "ledger" / "signing-key.pem"


def checkpoint_folder(settings: Settings) -> Path:
    return settings.data_dir / "ledger" / "checkpoints"


def _plural(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _unreadable(what: str, path: Path, error: OSError) -> str:
    return f"Could not read the {what} at {path}: {error.strerror}."


def _key_problem(what: str, path: Path, error: OSError | UnusableKey) -> str:
    """Why a key file can't be used. An UnusableKey's message names the file and never repeats
    a parser's text, which could quote the file's contents."""
    return _unreadable(what, path, error) if isinstance(error, OSError) else str(error)


def _is_in_the_way(error: OSError, files: set[Path]) -> bool:
    return (
        isinstance(error, FileExistsError)
        and error.filename is not None
        and (Path(error.filename) in files)
    )


def keygen(settings: Settings) -> int:
    path = key_file(settings)
    try:
        public = write_key_pair(Ed25519PrivateKey.generate(), path)
    except OSError as error:  # write_key_pair removes what it had created
        # Only a key file in the way means "already exists": a key folder that is a regular
        # file raises FileExistsError too (on Windows, for any folder above the key).
        if _is_in_the_way(error, {path, public_key_path(path)}):
            print(f"Not creating a signing key: {error.filename} already exists. Nothing changed.")
            return 1
        print(f"Could not create the signing key at {path}: {error.strerror}.")
        return 1
    print(f"Created the ledger signing key at {path}: keep it secret and back it up.")
    print(f"Its public key is at {public}: give that to anyone who checks the ledger.")
    return 0


async def make_checkpoint(settings: Settings, slug: str, folder: Path | None) -> int:
    path = key_file(settings)
    try:
        if not path.is_file():
            if os.path.lexists(path):  # a directory or a link to nothing: keygen would refuse it
                print(f"The ledger signing key path {path} is not a key file.")
            else:
                print(f"No ledger signing key at {path}: create one with `just ledger keygen`.")
            return 1
        private_key = load_private_key(path)
    except (OSError, UnusableKey) as error:
        print(_key_problem("ledger signing key", path, error))
        return 1
    database = Database(settings.database_url.get_secret_value())
    try:
        org_id = await database.org_id(slug)
        if org_id is None:
            print(f"There is no organisation {slug!r}.")
            return 1
        async with database.org_session(org_id) as session:
            signed = await checkpoint(session, private_key)
    except FourceError as error:
        print(error.message)
        return 1
    except OperationalError:
        print(_NOT_SET_UP)
        return 1
    finally:
        await database.dispose()
    # The entry is already committed: show the checkpoint before writing, so a full disk
    # can't lose the only copy of the signature.
    text = json.dumps(signed.to_dict(), indent=2)
    print(text)
    target = folder or checkpoint_folder(settings)
    file = target / f"{slug}-{signed.seq:010d}.json"
    try:
        target.mkdir(parents=True, exist_ok=True)
        # "x": never over an existing file, or a cut chain could hide behind a fresh checkpoint.
        with file.open("x", encoding="utf-8") as handle:
            handle.write(text + "\n")
    except FileExistsError as error:
        print(
            f"The checkpoint entry was recorded, but its file was not saved because "
            f"{error.filename} already exists and was left as it is. Keep the JSON above."
        )
        return 1
    except OSError as error:
        print(
            f"The checkpoint entry was recorded, but its file {file} could not be saved "
            f"({error.strerror}). Keep the JSON above."
        )
        return 1
    print(f"Signed entry {signed.seq} of {slug}, saved to {file}. Keep a copy off this machine.")
    return 0


def _read_checkpoints(folder: Path, org: str) -> list[Checkpoint]:
    """A missing folder holds none; anything that can't be read is an error, because skipping
    it could hide the one checkpoint that shows a cut chain."""
    found: list[Checkpoint] = []
    try:
        # A link to nothing (removable media not mounted) is not a missing folder.
        files = sorted(folder.iterdir()) if folder.is_symlink() or folder.exists() else []
    except OSError as error:  # unlike glob, which skips a folder it may not list
        raise ValueError(f"{folder} could not be read: {error.strerror}") from error
    for file in files:
        if file.suffix != ".json":
            continue
        try:
            read = Checkpoint.from_dict(json.loads(file.read_text(encoding="utf-8")))
        except OSError as error:
            raise ValueError(f"{file} could not be read: {error.strerror}") from error
        except (ValueError, RecursionError) as error:  # RecursionError: JSON nested too deep
            raise ValueError(f"{file} is not a checkpoint: {error}") from error
        if read.org == org:
            found.append(read)
    return found


def _report(slug: str, result: Verification, public_path: Path) -> int:
    print(
        f"Ledger of {slug}: {_plural(result.entries, 'entry', 'entries')}, head {result.head_seq}."
    )
    if result.anchored_seq is not None:
        print(f"A signed checkpoint vouches for it up to entry {result.anchored_seq}.")
        if result.uncovered_entries:
            print(
                f"Entries after {result.anchored_seq} are not covered by any checkpoint and "
                "cannot be shown intact; make a new checkpoint to extend the cover."
            )
    if result.unchecked_signatures:
        count = _plural(result.unchecked_signatures, "signature", "signatures")
        print(f"{count} not checked: no public key at {public_path} (or give --public-key).")
    if result.ok and result.anchored_seq is None:
        # Exit 0 must not be read as proof that the tail is intact.
        if result.unchecked_signatures:
            print("The chain's length is not proven: without the public key no checkpoint counts.")
        else:
            print(
                "The chain's length is not proven: nothing is anchored, so a cut-off tail "
                "can't be detected. Keep a checkpoint file off the machine and verify "
                "against it."
            )
    for problem in result.problems:
        print(f"  entry {problem.seq}: {problem.kind}: {problem.message}")
    if result.complete:
        if result.anchored_seq is not None and result.uncovered_entries:
            print(
                f"Verified through entry {result.anchored_seq}; "
                "entries after it are not covered by any checkpoint."
            )
        else:
            print("Verified.")
        return VERIFIED
    print("Failed." if not result.ok else "Incomplete: nothing wrong found, but not all checked.")
    return FAILED if not result.ok else INCOMPLETE


async def verify(
    settings: Settings, slug: str, public_key_file: Path | None, folder: Path | None
) -> int:
    public_path = public_key_file or public_key_path(key_file(settings))
    try:
        if public_key_file is not None and not public_key_file.is_file():
            print(f"No public key at {public_key_file}.")
            return FAILED
    except OSError as error:
        print(_unreadable("public key", public_path, error))
        return FAILED
    try:
        if folder is not None and not folder.is_dir():
            print(f"No checkpoint folder at {folder}.")
            return FAILED
    except OSError as error:
        print(_unreadable("checkpoint folder", folder or checkpoint_folder(settings), error))
        return FAILED
    try:
        public_key = load_public_key(public_path) if public_path.is_file() else None
    except (OSError, UnusableKey) as error:
        print(_key_problem("public key", public_path, error))
        return FAILED
    database = Database(settings.database_url.get_secret_value())
    try:
        org_id = await database.org_id(slug)
        if org_id is None:
            print(f"There is no organisation {slug!r}.")
            return FAILED
        found = _read_checkpoints(folder or checkpoint_folder(settings), str(org_id))
        async with database.org_session(org_id) as session:
            result = await verify_ledger(session, public_key=public_key, checkpoints=found)
    except ValueError as error:
        print(error)
        return FAILED
    except OperationalError:
        print(_NOT_SET_UP)
        return FAILED
    finally:
        await database.dispose()
    return _report(slug, result, public_path)
