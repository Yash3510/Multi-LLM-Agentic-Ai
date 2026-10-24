from fource.common import FourceError


class EmptyLedger(FourceError):
    code = "ledger_empty"
    status = 409


class UnreadableEntry(FourceError):
    """The database could not hand over a stored entry at all (not merely a strange one).
    Rows arrive in batches, so `seq`, the entry after the last one read, is where checking
    stopped, not necessarily the bad row."""

    code = "ledger_unreadable"
    status = 500

    def __init__(self, seq: int) -> None:
        super().__init__(f"The database could not return the entries from {seq} on.")
        self.seq = seq


class UnusableKey(ValueError):
    """A key file that can't serve as the installation's key. The message names the file and
    says why, and never repeats a parser's text, which could quote what it read."""
