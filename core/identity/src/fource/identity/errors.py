from fource.common import FourceError


class InvalidCredentials(FourceError):
    code = "invalid_credentials"
    status = 401


class AccountLocked(FourceError):
    code = "account_locked"
    status = 423


class NotAuthenticated(FourceError):
    code = "not_authenticated"
    status = 401


class WeakPassword(FourceError):
    code = "weak_password"
    status = 422


class InvalidEmail(FourceError):
    code = "invalid_email"
    status = 422


class EmailTaken(FourceError):
    code = "email_taken"
    status = 409


class InvalidDisplayName(FourceError):
    code = "validation_failed"
    status = 422
