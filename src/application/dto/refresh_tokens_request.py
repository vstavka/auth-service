from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshTokensRequest:
    refresh_token: str
