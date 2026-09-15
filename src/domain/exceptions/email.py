from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode


class InvalidEmailError(AppError):
    def __init__(self, reason: str | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_INVALID_EMAIL,
            message="Invalid email",
            details={"reason": reason} if reason else None,
        )
