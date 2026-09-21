import pytest

from src.domain.exceptions.password import InvalidPasswordError
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestInvalidPasswordError:
    def test_invalid_password_error_default_details_is_none(self) -> None:
        error = InvalidPasswordError()

        assert error.details is None
        assert error.code is ErrorCode.AUTH_INVALID_PASSWORD
        assert error.message == "Invalid password"

    def test_invalid_password_error_passes_details_to_base(self) -> None:
        details = {"reason": "too_short"}
        error = InvalidPasswordError(details=details)

        assert error.details == details
