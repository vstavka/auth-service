from datetime import timedelta

from src.application.dto import AccessTokenPayload, TokenPair
from src.application.ports.security import TokenService
from src.application.ports.system import Clock
from src.domain.exceptions.base import AppError
from src.domain.value_objects import UserId
from src.shared.errors.codes import ErrorCode


class FakeTokenService(TokenService):
    def __init__(
            self,
            *,
            clock: Clock,
            access_token_ttl: timedelta = timedelta(minutes=15),
            refresh_token_ttl: timedelta = timedelta(days=7),
    ) -> None:
        self._clock = clock
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl

        self._counter = 0
        self._access_tokens: dict[str, AccessTokenPayload] = {}

        self.issued_account_ids: list[UserId] = []
        self.issued_refresh_tokens: list[str] = []

    def issue_tokens(
            self,
            account_id: UserId,
    ) -> TokenPair:
        now = self._clock.now()

        access_expires_at = now + self._access_token_ttl
        refresh_expires_at = now + self._refresh_token_ttl

        self._counter += 1

        access_token = (
            f"fake-access:{account_id.value}:{self._counter}"
        )
        refresh_token = (
            f"fake-refresh:{account_id.value}:{self._counter}"
        )

        self._access_tokens[access_token] = AccessTokenPayload(
            account_id=account_id,
            expires_at=access_expires_at,
        )
        self.issued_account_ids.append(account_id)
        self.issued_refresh_tokens.append(refresh_token)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at,
        )

    def verify_access_token(
            self,
            access_token: str,
    ) -> AccessTokenPayload:
        payload = self._access_tokens.get(access_token)

        if payload is None:
            raise AppError(
                code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
                message="Access token is invalid or expired",
            )

        if payload.expires_at <= self._clock.now():
            raise AppError(
                code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
                message="Access token is invalid or expired",
            )

        return payload

    def hash_refresh_token(
            self,
            refresh_token: str,
    ) -> str:
        return f"fake-refresh-hash:{refresh_token}"
