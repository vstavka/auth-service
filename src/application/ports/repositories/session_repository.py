from typing import Protocol

from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId


class SessionRepository(Protocol):
    async def add(self, session: Session) -> None:
        """Добавляет новую сессию в текущую транзакцию."""

    async def get_by_public_id(self, public_id: SessionId) -> Session | None:
        """Возвращает сессию по публичному идентификатору."""

    async def get_by_refresh_token_hash(
            self,
            token_hash: RefreshTokenHash,
    ) -> Session | None:
        """Возвращает сессию по хешу refresh token."""

    async def list_by_account_id(self, account_id: int) -> list[Session]:
        """Возвращает сессии аккаунта."""

    async def save(self, session: Session) -> None:
        """Сохраняет изменения существующей сессии."""
