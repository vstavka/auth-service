from typing import Any

from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode


class InvalidPasswordError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_INVALID_PASSWORD,
            message="Invalid password",
            details=details,
        )
