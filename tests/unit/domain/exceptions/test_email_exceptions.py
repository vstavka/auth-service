import pytest

from src.domain.exceptions.email import (
    EmailAlreadyRegisteredError,
    InvalidEmailError,
)
from src.shared.errors.codes import ErrorCode


@pytest.mark.unit
class TestInvalidEmailError:
    def test_invalid_email_error_without_details(self) -> None:
        error = InvalidEmailError()

        assert error.details is None

    def test_invalid_email_error_with_details(self) -> None:
        error = InvalidEmailError(details={"reason": "bad format"})

        assert error.details == {"reason": "bad format"}
        assert error.code is ErrorCode.AUTH_INVALID_EMAIL
        assert error.message == "Invalid email"


@pytest.mark.unit
class TestEmailAlreadyRegisteredError:
    def test_email_already_registered_without_details(self) -> None:
        error = EmailAlreadyRegisteredError()

        assert error.details is None

    def test_email_already_registered_with_details(self) -> None:
        error = EmailAlreadyRegisteredError(details={"email": "user@example.com"})

        assert error.details == {"email": "user@example.com"}

    def test_email_already_registered_code_and_message(self) -> None:
        error = EmailAlreadyRegisteredError()

        assert error.code is ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED
        assert error.message == "Email already registered"
