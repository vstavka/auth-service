import pytest

from src.domain.exceptions.email import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
)
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestInvalidEmailError:
    def test_invalid_email_error_without_reason_has_no_details(self) -> None:
        error = InvalidEmailError()

        assert error.details is None

    def test_invalid_email_error_with_reason_in_details(self) -> None:
        error = InvalidEmailError(reason="bad format")

        assert error.details == {"reason": "bad format"}
        assert error.code is ErrorCode.AUTH_INVALID_EMAIL
        assert error.message == "Invalid email"


@pytest.mark.unit
class TestEmailAlreadyRegisteredError:
    def test_email_already_registered_without_reason_has_no_details(self) -> None:
        error = EmailAlreadyRegisteredError()

        assert error.details is None

    def test_email_already_registered_with_reason_in_details(self) -> None:
        error = EmailAlreadyRegisteredError(reason="unique constraint")

        assert error.details == {"reason": "unique constraint"}

    def test_email_already_registered_code_and_message(self) -> None:
        error = EmailAlreadyRegisteredError()

        assert error.code is ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED
        assert error.message == "Email already registered"
