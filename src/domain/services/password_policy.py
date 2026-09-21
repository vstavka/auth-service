import re
from dataclasses import dataclass

from src.domain.exceptions.password import InvalidPasswordError


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    min_length: int = 12
    max_length: int = 128

    def validate(self, raw_password: str) -> None:
        if len(raw_password) < self.min_length:
            raise InvalidPasswordError(
                details={"min_length": self.min_length, "reason": "too_short"},
            )

        if len(raw_password) > self.max_length:
            raise InvalidPasswordError(
                details={"max_length": self.max_length, "reason": "too_long"},
            )

        if not re.search(r"[a-zа-яё]", raw_password, re.IGNORECASE):
            raise InvalidPasswordError(details={"reason": "no_letter"})

        if not re.search(r"\d", raw_password):
            raise InvalidPasswordError(details={"reason": "no_digit"})

        if not re.search(r"[^a-zA-Zа-яА-ЯёЁ0-9\s]", raw_password):
            raise InvalidPasswordError(details={"reason": "no_special_character"})
