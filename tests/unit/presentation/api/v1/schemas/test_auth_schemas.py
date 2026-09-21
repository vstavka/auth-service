from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.application.dto import AccountPublic, SessionPublic
from src.domain.enums import AccountStatus
from src.presentation.api.v1.schemas.account import (
    ChangeEmailBody,
    ChangePasswordBody,
    account_public_to_schema,
)
from src.presentation.api.v1.schemas.auth import (
    LoginAccountRequest,
    RefreshTokensBody,
    RegisterAccountRequest,
    login_request_to_application,
    refresh_tokens_to_application,
    register_request_to_application,
)
from src.presentation.api.v1.schemas.session import session_public_to_schema


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
        assert command.ip is None
        assert command.user_agent is None

    def test_register_request_to_application_maps_client_metadata(self) -> None:
        payload = RegisterAccountRequest(
            email="user@example.com",
            password="secret1",
        )

        command = register_request_to_application(
            payload,
            ip="127.0.0.1",
            user_agent="pytest",
        )

        assert command.ip == "127.0.0.1"
        assert command.user_agent == "pytest"

    def test_register_account_request_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="not-an-email", password="secret1")

    def test_register_account_request_rejects_password_out_of_bounds(self) -> None:
        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="user@example.com", password="12345")

        with pytest.raises(ValidationError):
            RegisterAccountRequest(email="user@example.com", password="x" * 65)


@pytest.mark.unit
class TestLoginAndRefreshSchemas:
    def test_login_request_to_application_maps_fields(self) -> None:
        payload = LoginAccountRequest(
            email="User@Example.COM",
            password="secret1",
        )

        command = login_request_to_application(
            payload,
            ip="10.0.0.1",
            user_agent="agent",
        )

        assert command.email == "User@example.com"
        assert command.password == "secret1"
        assert command.ip == "10.0.0.1"
        assert command.user_agent == "agent"

    def test_refresh_tokens_to_application_maps_token(self) -> None:
        command = refresh_tokens_to_application(
            RefreshTokensBody(refresh_token="raw-refresh"),
        )

        assert command.refresh_token == "raw-refresh"

    def test_refresh_tokens_body_rejects_empty_token(self) -> None:
        with pytest.raises(ValidationError):
            RefreshTokensBody(refresh_token="")


@pytest.mark.unit
class TestAccountAndSessionSchemas:
    def test_account_public_to_schema(self) -> None:
        now = datetime.now(tz=UTC)
        schema = account_public_to_schema(
            AccountPublic(
                id=UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
                email="user@example.com",
                status=AccountStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            ),
        )

        assert schema.email == "user@example.com"
        assert schema.status == AccountStatus.ACTIVE

    def test_session_public_to_schema(self) -> None:
        now = datetime.now(tz=UTC)
        schema = session_public_to_schema(
            SessionPublic(
                id=UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"),
                ip="127.0.0.1",
                user_agent="pytest",
                device_info=None,
                created_at=now,
                expires_at=now,
                revoked_at=None,
            ),
        )

        assert schema.ip == "127.0.0.1"
        assert schema.revoked_at is None

    def test_change_email_body_rejects_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            ChangeEmailBody(email="not-an-email")

    def test_change_password_body_rejects_short_new_password(self) -> None:
        with pytest.raises(ValidationError):
            ChangePasswordBody(current_password="old", new_password="12345")
