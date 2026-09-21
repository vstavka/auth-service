from typing import Any

from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode


class InvalidEmailError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_INVALID_EMAIL,
            message="Invalid email",
            details=details,
        )


class EmailAlreadyRegisteredError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED,
            message="Email already registered",
            details=details,
        )
