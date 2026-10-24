"""Signed checkpoints of a chain head, and the installation's Ed25519 key (ADR-0014).

No database here either: an auditor's verifier needs only these functions and the public key.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)

from fource.ledger.chain import canonical, sha256_hex

# Signed bytes start with this, so a checkpoint signature can never be passed off as a
# signature over anything else the same key might sign.
CONTEXT = b"4ce-ledger-checkpoint-v1\n"
_HEX = re.compile(r"[0-9a-f]+")


@dataclass(frozen=True)
class Checkpoint:
    """The head of one organisation's chain (entry `seq`, with hash `hash`) at time `at`,
    signed with the key whose id is `key`. `signature` is the Ed25519 signature in hex."""

    org: str
    seq: int
    hash: str
    at: str
    key: str
    signature: str

    def signed_bytes(self) -> bytes:
        body = {"org": self.org, "seq": self.seq, "hash": self.hash, "at": self.at}
        return CONTEXT + canonical({**body, "key": self.key})

    def to_dict(self) -> dict[str, object]:
        return {
            "org": self.org,
            "seq": self.seq,
            "hash": self.hash,
            "at": self.at,
            "key": self.key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Checkpoint":
        """A checkpoint read from a file; ValueError if it isn't one."""
        if not isinstance(data, dict):
            raise ValueError("a checkpoint is a JSON object")
        fields = cast("dict[str, object]", data)
        seq = fields.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 1:
            raise ValueError("a checkpoint's seq is a whole number counting from 1")
        texts: dict[str, str] = {}
        for name in ("org", "hash", "at", "key", "signature"):
            value = fields.get(name)
            if not isinstance(value, str):
                raise ValueError(f"a checkpoint's {name} is text")
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                raise ValueError(f"a checkpoint's {name} is not valid text") from None
            texts[name] = value
        return cls(seq=seq, **texts)


def key_id(public_key: Ed25519PublicKey) -> str:
    """The SHA-256 of the raw 32-byte public key, in hex: names the key in every checkpoint."""
    return sha256_hex(public_key.public_bytes(Encoding.Raw, PublicFormat.Raw))


def sign_checkpoint(
    private_key: Ed25519PrivateKey, *, org: str, seq: int, hash: str, at: str
) -> Checkpoint:
    unsigned = Checkpoint(
        org=org, seq=seq, hash=hash, at=at, key=key_id(private_key.public_key()), signature=""
    )
    signature = private_key.sign(unsigned.signed_bytes()).hex()
    return Checkpoint(org=org, seq=seq, hash=hash, at=at, key=unsigned.key, signature=signature)


def is_signed_by(checkpoint: Checkpoint, public_key: Ed25519PublicKey) -> bool:
    """True only when this key made this exact checkpoint."""
    if checkpoint.key != key_id(public_key) or not _HEX.fullmatch(checkpoint.signature):
        return False
    if len(checkpoint.signature) % 2:
        return False
    try:
        public_key.verify(bytes.fromhex(checkpoint.signature), checkpoint.signed_bytes())
    except (InvalidSignature, ValueError, TypeError):
        return False
    return True


def public_key_path(private_key_path: Path) -> Path:
    """signing-key.pem -> signing-key.pub.pem, next to it."""
    return private_key_path.with_name(f"{private_key_path.stem}.pub{private_key_path.suffix}")


def _create(path: Path, data: bytes, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(path, flags, mode), "wb") as file:
        file.write(data)


def write_key_pair(private_key: Ed25519PrivateKey, path: Path) -> Path:
    """Writes the private key (PEM, readable by its owner only) and the public key next to it.

    Never overwrites either file, nor writes through a symlink: losing a private key would
    orphan every checkpoint it signed. If a write fails, what this call created is removed.
    Returns the public key's path.
    """
    public = public_key_path(path)
    for target in (path, public):
        if os.path.lexists(target):
            raise FileExistsError(f"{target} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    public_pem = private_key.public_key().public_bytes(
        Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
    )
    created: list[Path] = []
    try:
        _create(path, pem, 0o600)
        created.append(path)
        _create(public, public_pem, 0o644)
        created.append(public)
    except BaseException:
        for file in created:
            file.unlink(missing_ok=True)
        raise
    return public


def load_private_key(path: Path) -> Ed25519PrivateKey:
    try:
        key = load_pem_private_key(path.read_bytes(), password=None)
    except TypeError:
        raise ValueError(f"{path} is password-protected, which 4CE does not use") from None
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"{path} does not hold an Ed25519 private key")
    return key


def load_public_key(path: Path) -> Ed25519PublicKey:
    key = load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError(f"{path} does not hold an Ed25519 public key")
    return key
