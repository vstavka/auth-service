from typing import Protocol

from src.domain.value_objects import PasswordHash


class PasswordHasher(Protocol):
    def hash(self, raw_password: str) -> PasswordHash:
        """Создаёт безопасный хеш пароля."""

    def verify(
            self,
            raw_password: str,
            password_hash: PasswordHash,
    ) -> bool:
        """Возвращает True, если пароль соответствует хешу."""
