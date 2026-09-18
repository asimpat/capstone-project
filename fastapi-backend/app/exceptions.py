from typing import Any


class APIException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[Any] | None = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []

        super().__init__(message)
