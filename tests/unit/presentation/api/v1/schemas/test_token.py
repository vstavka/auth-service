from datetime import UTC, datetime, timedelta

import pytest

from src.application.dto import TokenPair
from src.presentation.api.v1.schemas.token import token_pair_to_schema


@pytest.mark.unit
class TestTokenPairToSchema:
    def test_token_pair_to_schema_maps_tokens_and_type(self) -> None:
        now = datetime.now(UTC)
        token_pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            access_token_expires_at=now + timedelta(minutes=15),
            refresh_token_expires_at=now + timedelta(days=7),
            token_type="bearer",
        )

        schema = token_pair_to_schema(token_pair)

        assert schema.access_token == "access"
        assert schema.refresh_token == "refresh"
        assert schema.token_type == "bearer"

    def test_token_pair_to_schema_expires_in_positive(self) -> None:
        now = datetime.now(UTC)
        token_pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            access_token_expires_at=now + timedelta(minutes=15),
            refresh_token_expires_at=now + timedelta(days=7),
        )

        assert token_pair_to_schema(token_pair).expires_in > 0

    def test_token_pair_to_schema_expires_in_zero_when_access_expired(self) -> None:
        now = datetime.now(UTC)
        token_pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            access_token_expires_at=now - timedelta(minutes=1),
            refresh_token_expires_at=now + timedelta(days=7),
        )

        assert token_pair_to_schema(token_pair).expires_in == 0

    def test_token_pair_to_schema_propagates_custom_token_type(self) -> None:
        now = datetime.now(UTC)
        token_pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            access_token_expires_at=now + timedelta(minutes=15),
            refresh_token_expires_at=now + timedelta(days=7),
            token_type="custom",
        )

        assert token_pair_to_schema(token_pair).token_type == "custom"
