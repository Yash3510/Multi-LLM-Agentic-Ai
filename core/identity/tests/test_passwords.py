import pytest

from fource.identity import WeakPassword, hash_password, needs_rehash, verify_password
from fource.identity.passwords import rehash

GOOD = "correct horse battery"


def test_passwords_hash_with_argon2id_and_verify() -> None:
    stored = hash_password(GOOD)
    assert stored.startswith("$argon2id$")
    assert verify_password(stored, GOOD)
    assert not verify_password(stored, "wrong horse battery")
    assert not needs_rehash(stored)


def test_a_damaged_hash_never_verifies() -> None:
    assert not verify_password("not-a-hash", GOOD)


@pytest.mark.parametrize("password", ["short", "x" * 1025])
def test_password_length_is_bounded(password: str) -> None:
    with pytest.raises(WeakPassword):
        hash_password(password)


# A lone surrogate can't be encoded as UTF-8; the password functions must not crash on it.
UNENCODABLE = "\ud800" * 12


def test_a_password_that_cannot_be_encoded_never_verifies() -> None:
    assert not verify_password(hash_password(GOOD), UNENCODABLE)


def test_a_password_that_cannot_be_encoded_is_too_weak_to_hash() -> None:
    with pytest.raises(WeakPassword):
        hash_password(UNENCODABLE)
    with pytest.raises(WeakPassword):
        rehash(UNENCODABLE)
