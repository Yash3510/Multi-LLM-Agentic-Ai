from fource.common import FourceError


class EmptyLedger(FourceError):
    code = "ledger_empty"
    status = 409
