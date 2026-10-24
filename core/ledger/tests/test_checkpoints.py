import os
from pathlib import Path
from typing import cast

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    PrivateFormat,
)

from fource.ledger import (
    Checkpoint,
    is_signed_by,
    key_id,
    load_private_key,
    load_public_key,
    public_key_path,
    sign_checkpoint,
    write_key_pair,
)

ORG = "0192f5a0-0000-7000-8000-000000000001"
AT = "2026-11-14T10:22:31.512Z"


def signed(key: Ed25519PrivateKey) -> Checkpoint:
    return sign_checkpoint(key, org=ORG, seq=7, hash="a" * 64, at=AT)


def test_a_checkpoint_verifies_with_its_key_only() -> None:
    key, other = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    checkpoint = signed(key)
    assert checkpoint.key == key_id(key.public_key()) and len(checkpoint.signature) == 128
    assert is_signed_by(checkpoint, key.public_key())
    assert not is_signed_by(checkpoint, other.public_key())


@pytest.mark.parametrize(
    "field, value",
    [("org", "another"), ("seq", 8), ("hash", "b" * 64), ("at", "2026-11-14T10:22:31.513Z")],
)
def test_changing_any_signed_field_breaks_the_signature(field: str, value: object) -> None:
    key = Ed25519PrivateKey.generate()
    data = {**signed(key).to_dict(), field: value}
    assert not is_signed_by(Checkpoint.from_dict(data), key.public_key())


@pytest.mark.parametrize("signature", ["", "zz", "abc", "00" * 64])
def test_a_garbled_signature_is_simply_invalid(signature: str) -> None:
    key = Ed25519PrivateKey.generate()
    data = {**signed(key).to_dict(), "signature": signature}
    assert not is_signed_by(Checkpoint.from_dict(data), key.public_key())


def test_a_checkpoint_round_trips_through_a_dict_and_refuses_bad_ones() -> None:
    checkpoint = signed(Ed25519PrivateKey.generate())
    assert Checkpoint.from_dict(checkpoint.to_dict()) == checkpoint
    for broken in [{**checkpoint.to_dict(), "seq": "7"}, {**checkpoint.to_dict(), "key": None}]:
        with pytest.raises(ValueError):
            Checkpoint.from_dict(broken)


def test_a_key_pair_is_written_once_and_read_back(tmp_path: Path) -> None:
    key = Ed25519PrivateKey.generate()
    path = tmp_path / "ledger" / "signing-key.pem"
    public = write_key_pair(key, path)
    assert public == public_key_path(path) == tmp_path / "ledger" / "signing-key.pub.pem"
    assert key_id(load_private_key(path).public_key()) == key_id(key.public_key())
    assert key_id(load_public_key(public)) == key_id(key.public_key())
    if os.name == "posix":  # Windows has no owner-only mode bits
        assert os.stat(path).st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_key_pair(Ed25519PrivateKey.generate(), path)
    assert key_id(load_private_key(path).public_key()) == key_id(key.public_key())


def test_a_checkpoint_that_cannot_be_encoded_is_refused_and_never_raises() -> None:
    key = Ed25519PrivateKey.generate()
    data = {**signed(key).to_dict(), "org": "\ud800"}
    with pytest.raises(ValueError):
        Checkpoint.from_dict(data)
    unsendable = Checkpoint(org="\ud800", seq=7, hash="a" * 64, at=AT, key="k", signature="00" * 64)
    assert not is_signed_by(unsendable, key.public_key())


@pytest.mark.parametrize("seq", [0, -1, True])
def test_a_checkpoint_seq_counts_from_one(seq: object) -> None:
    with pytest.raises(ValueError):
        Checkpoint.from_dict({**signed(Ed25519PrivateKey.generate()).to_dict(), "seq": seq})


def test_a_public_key_path_that_is_a_symlink_is_refused_and_its_target_untouched(
    tmp_path: Path,
) -> None:
    path = tmp_path / "signing-key.pem"
    target = tmp_path / "elsewhere.txt"
    target.write_text("keep")
    if os.name == "posix":
        public_key_path(path).symlink_to(target)
        with pytest.raises(FileExistsError):
            write_key_pair(Ed25519PrivateKey.generate(), path)
        assert target.read_text() == "keep"
        assert not path.exists()


def test_an_existing_public_key_is_not_replaced_and_nothing_is_written(tmp_path: Path) -> None:
    path = tmp_path / "signing-key.pem"
    public_key_path(path).write_text("stale")
    with pytest.raises(FileExistsError):
        write_key_pair(Ed25519PrivateKey.generate(), path)
    assert not path.exists()
    assert public_key_path(path).read_text() == "stale"


def test_a_password_protected_key_is_a_value_error(tmp_path: Path) -> None:
    path = tmp_path / "locked.pem"
    path.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, BestAvailableEncryption(b"throwaway")
        )
    )
    with pytest.raises(ValueError):
        load_private_key(path)


def test_a_failed_write_leaves_no_key_file_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def full_disk(*args: object, **kwargs: object) -> object:
        raise OSError("no space left on device")

    path = tmp_path / "signing-key.pem"
    monkeypatch.setattr(os, "fdopen", full_disk)
    with pytest.raises(OSError):
        write_key_pair(Ed25519PrivateKey.generate(), path)
    assert not path.exists() and not public_key_path(path).exists()


def test_a_checkpoint_built_with_a_non_text_signature_is_simply_invalid() -> None:
    key = Ed25519PrivateKey.generate()
    odd = Checkpoint(
        org=ORG,
        seq=7,
        hash="a" * 64,
        at=AT,
        key=key_id(key.public_key()),
        signature=cast("str", 123),
    )
    assert not is_signed_by(odd, key.public_key())
