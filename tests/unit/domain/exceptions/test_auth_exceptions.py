import pytest

from src.domain.exceptions.auth import (
    AccessTokenInvalidError,
    AccountDisabledError,
    InvalidCredentialsError,
    RefreshTokenInvalidError,
    SessionNotFoundError,
    UserNotFoundError,
)
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestAccessTokenInvalidError:
    def test_default_details_is_none(self) -> None:
        error = AccessTokenInvalidError()

        assert error.details is None
        assert error.code is ErrorCode.AUTH_ACCESS_TOKEN_INVALID
        assert error.message == "Access token is invalid or expired"

    def test_passes_details(self) -> None:
        error = AccessTokenInvalidError(details={"reason": "expired"})

        assert error.details == {"reason": "expired"}


@pytest.mark.unit
class TestInvalidCredentialsError:
    def test_default_code_and_message(self) -> None:
        error = InvalidCredentialsError()

        assert error.details is None
        assert error.code is ErrorCode.AUTH_INVALID_CREDENTIALS
        assert error.message == "Invalid credentials"


@pytest.mark.unit
class TestAccountDisabledError:
    def test_default_code_and_message(self) -> None:
        error = AccountDisabledError()

        assert error.code is ErrorCode.AUTH_ACCOUNT_DISABLED
        assert error.message == "Account is disabled"


@pytest.mark.unit
class TestUserNotFoundError:
    def test_default_code_and_message(self) -> None:
        error = UserNotFoundError()

        assert error.code is ErrorCode.USER_NOT_FOUND
        assert error.message == "User not found"


@pytest.mark.unit
class TestSessionNotFoundError:
    def test_default_code_and_message(self) -> None:
        error = SessionNotFoundError()

        assert error.code is ErrorCode.AUTH_SESSION_NOT_FOUND
        assert error.message == "Session not found"


@pytest.mark.unit
class TestRefreshTokenInvalidError:
    def test_default_code_and_message(self) -> None:
        error = RefreshTokenInvalidError()

        assert error.code is ErrorCode.AUTH_REFRESH_TOKEN_INVALID
        assert error.message == "Refresh token is invalid or expired"
