from collections.abc import Callable
from datetime import UTC, datetime


def _system() -> datetime:
    return datetime.now(UTC)


_source: Callable[[], datetime] = _system


def now() -> datetime:
    """The current time, aware and in UTC. Everything time-dependent asks here."""
    return _source()


def set_clock(source: Callable[[], datetime] | None) -> None:
    """Replace the clock (tests do, to move time); None restores the system clock."""
    global _source
    _source = source or _system
