import pytest
from pydantic import ValidationError

from src.presentation.api.v1.schemas.auth import (
    RegisterAccountRequest,
    register_request_to_application,
)


@pytest.mark.unit
class TestRegisterAccountRequest:
    def test_register_request_to_application_maps_email_and_password(self) -> None:
        payload = RegisterAccountRequest(
            email="User@Example.COM",
            password="secret1",
        )

        command = register_request_to_application(payload)

        assert command.email == "User@example.com"
        assert command.password == "secret1"

    def test_register_account_request_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="not-an-email", password="secret1")

    def test_register_account_request_rejects_password_out_of_bounds(self) -> None:
        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="user@example.com", password="12345")

        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="user@example.com", password="x" * 65)
