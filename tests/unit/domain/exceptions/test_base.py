import pytest

from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestAppError:
    def test_str_returns_message(self) -> None:
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="Something went wrong",
        )

        assert str(error) == "Something went wrong"

    def test_stores_code_message_and_details(self) -> None:
        details = {"field": "email"}
        error = AppError(
            code=ErrorCode.AUTH_INVALID_EMAIL,
            message="Invalid email",
            details=details,
        )

        assert error.code is ErrorCode.AUTH_INVALID_EMAIL
        assert error.message == "Invalid email"
        assert error.details == details

    def test_details_default_is_none(self) -> None:
        error = AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="boom",
        )

        assert error.details is None
