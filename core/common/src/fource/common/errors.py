class FourceError(Exception):
    """An error a person or a client can act on: a stable code, an HTTP status, a message.

    Subclasses set `code` and `status`; codes are never renamed once published.
    """

    code = "error"
    status = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
