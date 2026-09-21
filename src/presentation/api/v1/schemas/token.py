from pydantic import BaseModel, ConfigDict

from src.application.dto import TokenPair


class TokenPairSchema(BaseModel):
    """Response schema for issued access/refresh token pair."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def token_pair_to_schema(token_pair: "TokenPair") -> TokenPairSchema:
    from datetime import datetime, UTC

    now = datetime.now(UTC)
    expires_in = max(0, int((token_pair.access_token_expires_at - now).total_seconds()))

    return TokenPairSchema(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=expires_in,
    )
