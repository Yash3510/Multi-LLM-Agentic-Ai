from fource.common import FourceError


class StorageUnavailable(FourceError):
    """The file store can't be reached, or refused 4CE (credentials, a missing bucket). The
    message never names the endpoint, a key or a path."""

    code = "storage_unavailable"
    status = 503


class FileNotFound(FourceError):
    """No such file in this organisation, or it was deleted."""

    code = "file_not_found"
    status = 404


class FileTooLarge(FourceError):
    code = "file_too_large"
    status = 413


class FileDamaged(FourceError):
    """The bytes are missing, or differ from what was stored (size or SHA-256)."""

    code = "file_damaged"
    status = 500


class BlobMissing(Exception):
    """An adapter has no bytes for a key; the storage service reports that as FileDamaged."""
