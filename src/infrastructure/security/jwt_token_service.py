import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import SecretStr

from src.application.dto import AccessTokenPayload, TokenPair
from src.application.ports.security import TokenService
from src.application.ports.system import Clock
from src.domain.exceptions.base import AppError
from src.domain.value_objects import UserId
from src.shared.errors.codes import ErrorCode


class JWTTokenService(TokenService):
    ACCESS_TOKEN_TYPE = "access"

    def __init__(
            self,
            *,
            secret_key: str | SecretStr,
            clock: Clock,
            access_token_ttl: timedelta = timedelta(minutes=15),
            refresh_token_ttl: timedelta = timedelta(days=7),
            issuer: str = "auth-service",
            audience: str = "auth-api",
            algorithm: str = "HS256",
    ) -> None:
        if not secret_key:
            raise ValueError("secret_key must not be empty")

        if access_token_ttl <= timedelta():
            raise ValueError("access_token_ttl must be positive")

        if refresh_token_ttl <= timedelta():
            raise ValueError("refresh_token_ttl must be positive")

        self._secret_key = (
            secret_key.get_secret_value() if isinstance(secret_key, SecretStr) else secret_key
        )
        self._algorithm = algorithm
        self._clock = clock
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl
        self._issuer = issuer
        self._audience = audience

    @staticmethod
    def _truncate_to_seconds(value: datetime) -> datetime:
        return value.replace(microsecond=0)

    def issue_tokens(
            self,
            account_id: UserId,
    ) -> TokenPair:
        now = self._truncate_to_seconds(self._clock.now())
        access_token_expires_at = now + self._access_token_ttl
        refresh_token_expires_at = now + self._refresh_token_ttl

        access_token = self._create_access_token(
            account_id=account_id,
            issued_at=now,
            expires_at=access_token_expires_at,
        )
        refresh_token = secrets.token_urlsafe(48)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=refresh_token_expires_at,
        )

    def verify_access_token(
            self,
            access_token: str,
    ) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                jwt=access_token,
                key=self._secret_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": [
                        "sub",
                        "typ",
                        "iss",
                        "aud",
                        "iat",
                        "exp",
                    ],
                },
            )
        except InvalidTokenError as exc:
            raise AppError(
                code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
                message="Access token is invalid or expired",
            )

        if payload.get("typ") != self.ACCESS_TOKEN_TYPE:
            raise AppError(
                code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
                message="Access token is invalid or expired",
            )

        try:
            return AccessTokenPayload(
                account_id=UserId(UUID(payload["sub"])),
                expires_at=datetime.fromtimestamp(
                    payload["exp"],
                    tz=UTC,
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AppError(
                code=ErrorCode.AUTH_ACCESS_TOKEN_INVALID,
                message="Access token is invalid or expired",
            )

    def hash_refresh_token(
            self,
            refresh_token: str,
    ) -> str:
        return hashlib.sha256(
            refresh_token.encode("utf-8"),
        ).hexdigest()

    def _create_access_token(
            self,
            *,
            account_id: UserId,
            issued_at: datetime,
            expires_at: datetime,
    ) -> str:
        payload: dict[str, Any] = {
            "sub": str(account_id.value),
            "typ": self.ACCESS_TOKEN_TYPE,
            "iss": self._issuer,
            "aud": self._audience,
            "iat": issued_at,
            "exp": expires_at,
        }

        return jwt.encode(
            payload=payload,
            key=self._secret_key,
            algorithm=self._algorithm,
        )
