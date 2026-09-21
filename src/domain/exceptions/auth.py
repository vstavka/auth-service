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


class InvalidCredentialsError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            message="Invalid credentials",
            details=details,
        )


class AccountDisabledError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_ACCOUNT_DISABLED,
            message="Account is disabled",
            details=details,
        )


class UserNotFoundError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.USER_NOT_FOUND,
            message="User not found",
            details=details,
        )


class RefreshTokenInvalidError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_REFRESH_TOKEN_INVALID,
            message="Refresh token is invalid or expired",
            details=details,
        )


class SessionNotFoundError(AppError):
    def __init__(self, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            code=ErrorCode.AUTH_SESSION_NOT_FOUND,
            message="Session not found",
            details=details,
        )
