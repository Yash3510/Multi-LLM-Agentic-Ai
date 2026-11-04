"""Checks one organisation's chain, entry by entry, against its hashes and checkpoints.

Pure like chain.py and checkpoints.py: entries can come from the database or from a file.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import cast

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from fource.ledger.chain import GENESIS, Entry, EntryType, entry_hash
from fource.ledger.checkpoints import Checkpoint, is_signed_by

ALTERED = "altered"
BROKEN_LINK = "broken_link"
MISSING = "missing"
OUT_OF_ORDER = "out_of_order"
WRONG_ORG = "wrong_org"
BAD_CHECKPOINT = "bad_checkpoint"
CHECKPOINT_MISMATCH = "checkpoint_mismatch"
TRUNCATED = "truncated"
UNREADABLE = "unreadable"


@dataclass(frozen=True)
class Problem:
    seq: int
    kind: str
    message: str


@dataclass(frozen=True)
class Verification:
    """What a check found. `anchored_seq` is the last entry a valid outside checkpoint vouches
    for: entries after it are consistent, but a cut-off tail after it can't be seen.
    `uncovered_entries` counts those entries, leaving out checkpoint entries that validly sign
    something at or before `anchored_seq`: the newest checkpoint entry always follows the
    entry it signs, and losing it would lose no record of any action."""

    org: str
    entries: int
    head_seq: int
    head_hash: str
    anchored_seq: int | None
    unchecked_signatures: int
    problems: tuple[Problem, ...]
    uncovered_entries: int = 0

    @property
    def ok(self) -> bool:
        return not self.problems

    @property
    def complete(self) -> bool:
        """No problems, and nothing left unchecked ("could not check" is never a pass)."""
        return self.ok and self.unchecked_signatures == 0


def _is_seq(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _text(value: object) -> str:
    """A tampered row may hold anything: only text counts as text."""
    return value if isinstance(value, str) else ""


def _mapping(value: object) -> Mapping[str, str] | None:
    return cast("Mapping[str, str]", value) if isinstance(value, Mapping) else None


def _hash_matches(entry: Entry) -> bool:
    """False when the hash differs, or when the entry is too malformed to hash at all."""
    if _mapping(entry.refs) is None:
        return False  # fields() would convert a list of pairs into the object it came from
    try:
        return entry_hash(entry.fields()) == entry.hash
    except (TypeError, ValueError, AttributeError, RecursionError):
        return False


class ChainVerifier:
    """Feed entries in order with add(), then call finish(). Holds one entry at a time, so a
    chain of any length can be streamed through it.

    `checkpoints` are copies kept outside the database; they are what make a cut-off tail,
    or a chain rewritten from the start, detectable. Without `public_key` their signatures
    (and those of checkpoint entries) are counted as unchecked, never as valid.
    """

    def __init__(
        self,
        org: str,
        *,
        public_key: Ed25519PublicKey | None = None,
        checkpoints: Iterable[Checkpoint] = (),
    ) -> None:
        self.org = org
        self._key = public_key
        self._problems: list[Problem] = []
        self._count = 0
        self._seq = 0
        self._top = 0
        self._hash: str = GENESIS
        self._unchecked = 0
        self._anchored: int | None = None
        self._uncovered = 0
        self._outside: dict[int, list[Checkpoint]] = {}
        for checkpoint in checkpoints:
            if not _is_seq(checkpoint.seq):
                self._problem(0, BAD_CHECKPOINT, "a checkpoint's seq isn't a whole number from 1")
            elif checkpoint.org != org:
                self._problem(checkpoint.seq, WRONG_ORG, "a checkpoint of another organisation")
            elif self._signature_ok(checkpoint):
                self._outside.setdefault(checkpoint.seq, []).append(checkpoint)
            else:
                self._problem(checkpoint.seq, BAD_CHECKPOINT, "a checkpoint's signature is wrong")
        # Problems with the checkpoints themselves don't stop a good one anchoring the chain;
        # only a problem found in the entries does.
        self._setup_problems = len(self._problems)

    def _problem(self, seq: int, kind: str, message: str) -> None:
        self._problems.append(Problem(seq, kind, message))

    def _signature_ok(self, checkpoint: Checkpoint) -> bool:
        if self._key is None:
            self._unchecked += 1
            return True  # kept for the hash comparison; it can never anchor the chain
        return is_signed_by(checkpoint, self._key)

    def add(self, entry: Entry) -> None:
        """Checks one entry. Entries may have been tampered with, so any shape of entry is
        reported as a problem here, never raised."""
        self._count += 1
        expected = self._seq + 1
        seq = entry.seq if _is_seq(entry.seq) else expected
        if seq != entry.seq:
            self._problem(seq, ALTERED, "its sequence number isn't a whole number from 1")
        if entry.org != self.org:
            self._problem(seq, WRONG_ORG, "belongs to another organisation")
        if seq < expected:
            self._problem(seq, OUT_OF_ORDER, f"comes after entry {self._seq}")
        elif seq > expected:
            self._problem(seq, MISSING, f"entries {expected} to {seq - 1} are missing")
        if entry.prev != self._hash:
            self._problem(seq, BROKEN_LINK, "doesn't link to the entry before it")
        if not _hash_matches(entry):
            self._problem(seq, ALTERED, "its contents don't match its hash")
        signs_earlier = False
        if entry.type == EntryType.CHECKPOINT:
            signs_earlier = self._check_entry_checkpoint(entry, seq)
        for outside in self._outside.get(seq, ()):
            if outside.hash != entry.hash:
                self._problem(seq, CHECKPOINT_MISMATCH, "differs from what a checkpoint signed")
            elif self._key is not None and len(self._problems) == self._setup_problems:
                self._anchored = max(self._anchored or 0, seq)
                self._uncovered = 0
        if self._anchored is None or seq > self._anchored:
            covered = signs_earlier and self._anchored is not None and seq - 1 <= self._anchored
            self._uncovered += 0 if covered else 1
        # Carry on from what this entry says, so one bad entry is reported once, not again
        # for every entry after it.
        self._seq = seq
        self._top = max(self._top, seq)
        self._hash = _text(entry.hash)

    def _check_entry_checkpoint(self, entry: Entry, seq: int) -> bool:
        """A checkpoint entry signs the entry before it: its refs must say so, and the
        signature must be the installation key's. True if it does, with the key present."""
        refs = _mapping(entry.refs)
        if refs is None:
            self._problem(seq, BAD_CHECKPOINT, "doesn't sign the entry before it")
            return False
        if refs.get("seq") != str(seq - 1) or refs.get("hash") != entry.prev:
            self._problem(seq, BAD_CHECKPOINT, "doesn't sign the entry before it")
            return False
        signed = Checkpoint(
            org=_text(entry.org),
            seq=seq - 1,
            hash=_text(entry.prev),
            at=_text(entry.at),
            key=_text(refs.get("key")),
            signature=_text(refs.get("signature")),
        )
        if not self._signature_ok(signed):
            self._problem(seq, BAD_CHECKPOINT, "its signature is wrong")
            return False
        return self._key is not None

    def unreadable(self, seq: int) -> None:
        """The database could not return the entries from `seq` on, so none were checked."""
        self._problem(
            seq,
            UNREADABLE,
            "the database could not return it or the entries after it, so they were not checked",
        )

    def finish(self) -> Verification:
        for seq in sorted(self._outside):
            if seq > self._top:
                self._problem(
                    seq, TRUNCATED, f"a checkpoint signed entry {seq}, the last is {self._top}"
                )
        return Verification(
            org=self.org,
            entries=self._count,
            head_seq=self._top,
            head_hash=self._hash,
            anchored_seq=self._anchored,
            unchecked_signatures=self._unchecked,
            problems=tuple(self._problems),
            uncovered_entries=self._uncovered,
        )


def verify_chain(
    entries: Iterable[Entry],
    org: str,
    *,
    public_key: Ed25519PublicKey | None = None,
    checkpoints: Iterable[Checkpoint] = (),
) -> Verification:
    verifier = ChainVerifier(org, public_key=public_key, checkpoints=checkpoints)
    for entry in entries:
        verifier.add(entry)
    return verifier.finish()
