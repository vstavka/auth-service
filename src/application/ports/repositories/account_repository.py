from typing import Protocol

from src.domain.entities import Account
from src.domain.value_objects import Email, UserId


class AccountRepository(Protocol):
    async def add(self, account: Account) -> None:
        """Добавляет новый аккаунт в текущую транзакцию."""

    async def get_by_id(self, account_id: UserId) -> Account | None:
        """Возвращает аккаунт по идентификатору."""

    async def get_by_ids(self, account_ids: list[UserId]) -> list[Account]:
        """Возвращает найденные аккаунты по списку идентификаторов."""

    async def get_by_email(self, email: Email) -> Account | None:
        """Возвращает аккаунт по нормализованному email."""

    async def get_by_internal_id(self, account_id: int) -> Account | None:
        """Возвращает аккаунт по внутреннему числовому идентификатору."""

    async def save(self, account: Account) -> None:
        """Сохраняет изменения существующего аккаунта."""
