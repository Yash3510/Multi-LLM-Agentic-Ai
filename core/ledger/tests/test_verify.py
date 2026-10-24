from dataclasses import replace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from fource.ledger import (
    GENESIS,
    Checkpoint,
    Entry,
    EntryType,
    Verification,
    make_entry,
    sign_checkpoint,
    verify_chain,
)

ORG = "0192f5a0-0000-7000-8000-000000000001"
OTHER_ORG = "0192f5a0-0000-7000-8000-000000000002"
KEY = Ed25519PrivateKey.generate()
PUBLIC = KEY.public_key()


def chain(length: int, *, rewrite_from: int | None = None) -> list[Entry]:
    """A chain of `length` entries; from `rewrite_from` on, every entry is changed and every
    hash recomputed, as someone with database access but no signing key could do."""
    entries: list[Entry] = []
    prev = GENESIS
    for seq in range(1, length + 1):
        actor = "anonymous" if rewrite_from is not None and seq >= rewrite_from else "system"
        entry = make_entry(
            seq=seq,
            at=f"2026-11-14T10:22:{seq:02d}.000Z",
            org=ORG,
            type=EntryType.SIGNIN_SUCCESS,
            actor=actor,
            prev=prev,
        )
        entries.append(entry)
        prev = entry.hash
    return entries


def signed_head(entries: list[Entry]) -> Checkpoint:
    last = entries[-1]
    return sign_checkpoint(KEY, org=ORG, seq=last.seq, hash=last.hash, at=last.at)


def checkpoint_entry(entries: list[Entry], *, signer: Ed25519PrivateKey = KEY) -> Entry:
    """The entry `ledger checkpoint` appends: it signs the entry before it."""
    last = entries[-1]
    signed = sign_checkpoint(signer, org=ORG, seq=last.seq, hash=last.hash, at=last.at)
    refs = {
        "seq": str(last.seq),
        "hash": last.hash,
        "key": signed.key,
        "signature": signed.signature,
    }
    return make_entry(
        seq=last.seq + 1,
        at=last.at,
        org=ORG,
        type=EntryType.CHECKPOINT,
        actor="system",
        refs=refs,
        prev=last.hash,
    )


def kinds(result: Verification) -> set[str]:
    return {problem.kind for problem in result.problems}


def test_an_intact_chain_verifies_and_is_anchored_by_its_checkpoint() -> None:
    entries = chain(5)
    result = verify_chain(entries, ORG, public_key=PUBLIC, checkpoints=[signed_head(entries)])
    assert result.ok and result.complete
    assert (result.entries, result.head_seq, result.head_hash) == (5, 5, entries[-1].hash)
    assert result.anchored_seq == 5


def test_an_empty_chain_verifies_and_is_anchored_by_nothing() -> None:
    result = verify_chain([], ORG)
    assert result.complete and (result.entries, result.head_hash) == (0, GENESIS)
    assert result.anchored_seq is None


def test_an_edit_is_detected_at_that_entry_only() -> None:
    entries = chain(5)
    entries[2] = replace(entries[2], actor="anonymous")
    result = verify_chain(entries, ORG)
    assert [(p.seq, p.kind) for p in result.problems] == [(3, "altered")]


def test_a_deletion_is_detected() -> None:
    entries = chain(5)
    del entries[2]
    assert kinds(verify_chain(entries, ORG)) == {"missing", "broken_link"}


def test_reordering_is_detected() -> None:
    entries = chain(5)
    entries[1], entries[2] = entries[2], entries[1]
    assert {"out_of_order", "broken_link"} <= kinds(verify_chain(entries, ORG))


def test_a_cut_off_tail_is_detected_only_against_a_checkpoint() -> None:
    entries = chain(5)
    checkpoint = signed_head(entries)
    assert verify_chain(entries[:3], ORG).ok  # the chain alone can't tell
    cut = verify_chain(entries[:3], ORG, public_key=PUBLIC, checkpoints=[checkpoint])
    assert [(p.seq, p.kind) for p in cut.problems] == [(5, "truncated")]


def test_a_chain_rewritten_with_fresh_hashes_is_detected_by_a_checkpoint() -> None:
    checkpoint = signed_head(chain(5))
    rewritten = chain(5, rewrite_from=2)
    assert verify_chain(rewritten, ORG).ok  # consistent on its own
    result = verify_chain(rewritten, ORG, public_key=PUBLIC, checkpoints=[checkpoint])
    assert kinds(result) == {"checkpoint_mismatch"} and result.anchored_seq is None


def test_entries_or_checkpoints_of_another_organisation_are_problems() -> None:
    entries = chain(2)
    entries[1] = replace(entries[1], org=OTHER_ORG)
    assert "wrong_org" in kinds(verify_chain(entries, ORG))
    foreign = replace(signed_head(chain(2)), org=OTHER_ORG)
    assert kinds(verify_chain(chain(2), ORG, public_key=PUBLIC, checkpoints=[foreign])) == {
        "wrong_org"
    }


def test_a_checkpoint_signed_by_another_key_is_refused() -> None:
    entries = chain(3)
    forged = sign_checkpoint(
        Ed25519PrivateKey.generate(), org=ORG, seq=3, hash=entries[-1].hash, at=entries[-1].at
    )
    result = verify_chain(entries, ORG, public_key=PUBLIC, checkpoints=[forged])
    assert kinds(result) == {"bad_checkpoint"} and result.anchored_seq is None


def test_checkpoint_entries_are_checked_against_the_entry_before_them() -> None:
    entries = chain(3)
    good = [*entries, checkpoint_entry(entries)]
    assert verify_chain(good, ORG, public_key=PUBLIC).complete
    forged = [*entries, checkpoint_entry(entries, signer=Ed25519PrivateKey.generate())]
    assert kinds(verify_chain(forged, ORG, public_key=PUBLIC)) == {"bad_checkpoint"}


def test_without_the_public_key_signatures_are_unchecked_never_valid() -> None:
    entries = chain(3)
    with_entry = [*entries, checkpoint_entry(entries)]
    result = verify_chain(with_entry, ORG, checkpoints=[signed_head(entries)])
    assert result.ok and not result.complete
    assert (result.unchecked_signatures, result.anchored_seq) == (2, None)


def test_two_checkpoints_for_one_entry_must_both_match() -> None:
    entries = chain(3)
    other = sign_checkpoint(KEY, org=ORG, seq=3, hash="f" * 64, at=entries[-1].at)
    result = verify_chain(
        entries, ORG, public_key=PUBLIC, checkpoints=[signed_head(entries), other]
    )
    assert kinds(result) == {"checkpoint_mismatch"}


def test_malformed_entries_are_problems_and_never_crash() -> None:
    good = chain(4)
    changes: list[dict[str, object]] = [
        {"seq": "2"},
        {"seq": True},
        {"seq": -5},
        {"at": None},
        {"actor": "\ud800"},
        {"refs": {"a": "\ud800"}},
        {"refs": None},
        {"refs": {"a": object()}},
        {"hash": None},
        {"prev": 7},
        {"type": EntryType.CHECKPOINT, "refs": None},
    ]
    for change in changes:
        bad = replace(good[1], **change)
        result = verify_chain([good[0], bad, good[2], good[3]], ORG, public_key=PUBLIC)
        assert not result.ok, change
