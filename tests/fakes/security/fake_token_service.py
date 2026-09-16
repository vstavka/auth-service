from datetime import datetime, timedelta, UTC

from src.application.dto import TokenPair, AccessTokenPayload
from src.application.ports.security import TokenService
from src.application.ports.system import Clock
from src.domain.exceptions.base import AppError
from src.domain.value_objects import UserId
from src.shared.errors.codes import ErrorCode


class FakeTokenService(TokenService):

    def __init__(
            self,
            *,
            clock:Clock,
            access_token_ttl: timedelta = timedelta(minutes=15),
            refresh_token_ttl: timedelta = timedelta(days=7),
    ) -> None:
        self._clock = clock
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._counter = 0
        self._access_tokens: dict[str, AccessTokenPayload] = {}

    def issue_tokens(self, account_id: UserId) -> TokenPair:
        access_expires_at = self._clock.now() + self._access_token_ttl
        refresh_expires_at = self._clock.now()  + self._refresh_token_ttl

        access_token = f"fake-access:{account_id}:{self._counter}"

        refresh_token = f"fake-refresh:{account_id}:{self._counter}"

        self._access_tokens[access_token] = AccessTokenPayload(
            account_id=account_id,
            expires_at=access_expires_at,
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token,
                         expires_in=self._access_token_ttl.seconds)

    def verify_access_token(self, access_token: str) -> AccessTokenPayload:
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
