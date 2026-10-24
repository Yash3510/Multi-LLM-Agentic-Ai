"""The `fource-server ledger` commands: keygen, checkpoint and verify (ADR-0014).

Signing is for people: nothing in CI or the tests signs with a real installation key.
"""

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy.exc import OperationalError

from fource.common import FourceError, Settings
from fource.db import Database
from fource.ledger import (
    Checkpoint,
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


def keygen(settings: Settings) -> int:
    path = key_file(settings)
    try:
        public = write_key_pair(Ed25519PrivateKey.generate(), path)
    except FileExistsError:
        print(f"A signing key already exists at {path}; it was left as it is.")
        return 1
    print(f"Created the ledger signing key at {path}: keep it secret and back it up.")
    print(f"Its public key is at {public}: give that to anyone who checks the ledger.")
    return 0


async def make_checkpoint(settings: Settings, slug: str, folder: Path | None) -> int:
    path = key_file(settings)
    if not path.is_file():
        print(f"No ledger signing key at {path}: create one with `just ledger keygen`.")
        return 1
    try:
        private_key = load_private_key(path)
    except ValueError as error:
        print(error)
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
        file.write_text(text + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Could not save the checkpoint to {file} ({error.strerror}): keep the JSON above.")
        return 1
    print(f"Signed entry {signed.seq} of {slug}, saved to {file}. Keep a copy off this machine.")
    return 0


def _read_checkpoints(folder: Path, org: str) -> list[Checkpoint]:
    found: list[Checkpoint] = []
    for file in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            read = Checkpoint.from_dict(json.loads(file.read_text(encoding="utf-8")))
        except ValueError as error:
            raise ValueError(f"{file} is not a checkpoint: {error}") from error
        if read.org == org:
            found.append(read)
    return found


def _report(slug: str, result: Verification) -> int:
    print(f"Ledger of {slug}: {result.entries} entries, head {result.head_seq}.")
    if result.anchored_seq is None:
        print(
            "The chain's length is not proven: no signed checkpoint anchors it, so a cut-off "
            "tail can't be detected. Keep a checkpoint file off the machine and verify "
            "against it."
        )
    else:
        print(f"A signed checkpoint vouches for it up to entry {result.anchored_seq}.")
    if result.unchecked_signatures:
        print(f"{result.unchecked_signatures} signatures not checked: no public key.")
    for problem in result.problems:
        print(f"  entry {problem.seq}: {problem.kind}: {problem.message}")
    if result.complete:
        print("Verified.")
        return VERIFIED
    print("Failed." if not result.ok else "Incomplete: nothing wrong found, but not all checked.")
    return FAILED if not result.ok else INCOMPLETE


async def verify(
    settings: Settings, slug: str, public_key_file: Path | None, folder: Path | None
) -> int:
    public_path = public_key_file or public_key_path(key_file(settings))
    if public_key_file is not None and not public_key_file.is_file():
        print(f"No public key at {public_key_file}.")
        return FAILED
    database = Database(settings.database_url.get_secret_value())
    try:
        public_key = load_public_key(public_path) if public_path.is_file() else None
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
    return _report(slug, result)
