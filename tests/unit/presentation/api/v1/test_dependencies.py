from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from src.domain.exceptions.auth import AccessTokenInvalidError
from src.domain.value_objects import SessionId, UserId
from src.presentation.api.v1.dependencies import get_access_context
from tests.fakes.security.fake_token_service import FakeTokenService
from tests.fakes.system.fake_clock import FakeClock


@pytest.mark.unit
class TestGetAccessContext:
    @pytest.fixture
    def fake_token_service(self) -> FakeTokenService:
        clock = FakeClock(datetime.now(tz=UTC))
        service = FakeTokenService(clock=clock)
        service.issue_tokens(
            account_id=UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c")),
            session_id=SessionId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d")),
        )
        return service

    async def test_raises_when_credentials_missing(
            self,
            fake_token_service: FakeTokenService,
    ) -> None:
        with pytest.raises(AccessTokenInvalidError):
            await get_access_context(
                credentials=None,
                token_service=fake_token_service,
            )

    async def test_raises_when_scheme_is_not_bearer(
            self,
            fake_token_service: FakeTokenService,
    ) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Basic",
            credentials="abc",
        )

        with pytest.raises(AccessTokenInvalidError):
            await get_access_context(
                credentials=credentials,
                token_service=fake_token_service,
            )

    async def test_returns_payload_for_valid_bearer(
            self,
            fake_token_service: FakeTokenService,
    ) -> None:
        access_token = next(iter(fake_token_service._access_tokens))
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=access_token,
        )

        payload = await get_access_context(
            credentials=credentials,
            token_service=fake_token_service,
        )

        assert payload.account_id == UserId(
            UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
        )
        assert payload.session_id == SessionId(
            UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"),
        )
