from functools import cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from fource.identity.errors import WeakPassword

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024
_hasher = PasswordHasher()  # argon2id with the library's current parameters


def hash_password(password: str) -> str:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise WeakPassword(
            f"A password needs {MIN_PASSWORD_LENGTH} to {MAX_PASSWORD_LENGTH} characters."
        )
    return _hasher.hash(password)


def rehash(password: str) -> str:
    """A fresh hash of a password that already passed sign-in, whatever its length."""
    return _hasher.hash(password)


def verify_password(stored: str, password: str) -> bool:
    try:
        return _hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored: str) -> bool:
    return _hasher.check_needs_rehash(stored)


@cache
def timing_hash() -> str:
    """A real hash to verify against when an email is unknown, so timing reveals nothing."""
    return _hasher.hash("not a password anyone has; spent only to even out timing")
