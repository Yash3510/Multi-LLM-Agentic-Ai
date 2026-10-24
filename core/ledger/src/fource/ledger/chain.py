"""Ledger entries and their hash chain: pure functions, no database (ADR-0014).

Everything here uses the standard library only, so the verifier can later run on an
auditor's machine with nothing of 4CE but these files.
"""

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum

GENESIS = "0" * 64
SYSTEM = "system"
ANONYMOUS = "anonymous"

_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")
_TYPE = re.compile(r"[a-z]+(\.[a-z_]+)*")
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_ID = re.compile(_UUID)
_ACTOR = re.compile(rf"system|anonymous|user:{_UUID}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REF_KEY = re.compile(r"[a-z][a-z0-9_]{0,63}")
MAX_REF_LENGTH = 1000


class EntryType(StrEnum):
    """Every type of entry 4CE writes (master plan Appendix B; identity.* by ADR-0039).

    Each work package that adds an action adds its type here.
    """

    CHECKPOINT = "checkpoint"
    USER_CREATE = "identity.user.create"
    SIGNIN_SUCCESS = "identity.signin.success"
    SIGNIN_FAILURE = "identity.signin.failure"
    LOCKOUT = "identity.lockout"
    SIGNOUT = "identity.signout"


@dataclass(frozen=True)
class Entry:
    """One ledger entry, field for field as master plan Appendix B shows it."""

    seq: int
    at: str
    org: str
    run: str | None
    case: str | None
    type: str
    actor: str
    inputs_sha256: str | None
    outputs_sha256: str | None
    refs: Mapping[str, str] = field(hash=False)
    prev: str
    hash: str

    def fields(self) -> dict[str, object]:
        """Everything the hash covers: every field but the hash itself."""
        return {
            "seq": self.seq,
            "at": self.at,
            "org": self.org,
            "run": self.run,
            "case": self.case,
            "type": self.type,
            "actor": self.actor,
            "inputs_sha256": self.inputs_sha256,
            "outputs_sha256": self.outputs_sha256,
            "refs": dict(self.refs),
            "prev": self.prev,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.fields(), "hash": self.hash}


def canonical(value: Mapping[str, object]) -> bytes:
    """The one byte form that is hashed and signed: JSON with keys sorted, no spaces, UTF-8.

    Values are only strings, integers, null and objects of strings, so this matches RFC 8785
    (JSON Canonicalization Scheme) for every entry 4CE writes.
    """
    text = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return text.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entry_hash(fields: Mapping[str, object]) -> str:
    return sha256_hex(canonical(fields))


def to_millis(moment: datetime) -> datetime:
    """The moment in UTC, cut to whole milliseconds: what an entry's time can say."""
    if moment.tzinfo is None:
        raise ValueError("a time needs its time zone")
    moment = moment.astimezone(UTC)
    return moment.replace(microsecond=moment.microsecond // 1000 * 1000)


def format_time(moment: datetime) -> str:
    """ISO 8601 in UTC with milliseconds and a Z, as in Appendix B: 2026-11-14T10:22:31.512Z."""
    moment = to_millis(moment)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def user_actor(user_id: object) -> str:
    return f"user:{user_id}"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _matches(pattern: re.Pattern[str], value: object) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _is_seq(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _storable(text: object) -> bool:
    return isinstance(text, str) and "\x00" not in text and text.isprintable()


def _check_refs(refs: Mapping[str, str]) -> None:
    for key, value in refs.items():
        _require(_matches(_REF_KEY, key), f"a ref name is lower snake case: {key!r}")
        _require(
            _storable(value) and len(value) <= MAX_REF_LENGTH,
            f"ref {key!r} must be printable text of up to {MAX_REF_LENGTH}",
        )


def make_entry(
    *,
    seq: int,
    at: str,
    org: str,
    type: str,
    actor: str,
    prev: str,
    run: str | None = None,
    case: str | None = None,
    inputs_sha256: str | None = None,
    outputs_sha256: str | None = None,
    refs: Mapping[str, str] | None = None,
) -> Entry:
    """A checked entry with its hash. Raises ValueError for anything malformed, because a
    bad entry is a bug in the code writing it, never something to store."""
    _require(_is_seq(seq), "seq is a whole number counting from 1")
    _require(_matches(_TIME, at), f"at is UTC with milliseconds and a Z: {at!r}")
    _require(_matches(_ID, org), "org is a lower-case UUID")
    for name, value in (("run", run), ("case", case)):
        _require(value is None or _matches(_ID, value), f"{name} is a lower-case UUID")
    _require(_matches(_TYPE, type) and len(type) <= 64, f"not an entry type: {type!r}")
    _require(
        _matches(_ACTOR, actor), f"an actor is 'system', 'anonymous' or 'user:<uuid>': {actor!r}"
    )
    for name, value in (("inputs_sha256", inputs_sha256), ("outputs_sha256", outputs_sha256)):
        _require(value is None or _matches(_SHA256, value), f"{name} is 64 lower-case hex digits")
    _require(_matches(_SHA256, prev), "prev is 64 lower-case hex digits")
    checked = dict(refs or {})
    _check_refs(checked)
    draft = Entry(
        seq=seq,
        at=at,
        org=org,
        run=run,
        case=case,
        type=type,
        actor=actor,
        inputs_sha256=inputs_sha256,
        outputs_sha256=outputs_sha256,
        refs=checked,
        prev=prev,
        hash="",
    )
    return replace(draft, hash=entry_hash(draft.fields()))
