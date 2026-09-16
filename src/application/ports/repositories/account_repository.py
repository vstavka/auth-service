from typing import Protocol

from src.domain.entities import Account
from src.domain.value_objects import Email, UserId


class AccountRepository(Protocol):
    async def add(self, account: Account) -> None:
        """Добавляет новый аккаунт в текущую транзакцию."""

    async def get_by_id(self, account_id: UserId) -> Account | None:
        """Возвращает аккаунт по идентификатору."""

    async def get_by_email(self, email: Email) -> Account | None:
        """Возвращает аккаунт по нормализованному email."""
