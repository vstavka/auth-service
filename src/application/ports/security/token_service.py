from typing import Protocol

from src.application.dto import TokenPair, AccessTokenPayload
from src.domain.entities import Account
from src.domain.value_objects import UserId


class TokenService(Protocol):

    def issue_tokens(self,*,account_id: UserId) -> TokenPair:
        """Создаёт access- и refresh-токены для аккаунта."""

    def verify_access_token(self, access_token: str) -> AccessTokenPayload:
        """Проверить access token и вернуть данные после валидации."""
