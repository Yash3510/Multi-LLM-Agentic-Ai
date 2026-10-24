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
