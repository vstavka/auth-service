from typing import Any

from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode


class AccessTokenInvalidError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
            message="Access token is invalid or expired",
            details=details,
        )
