from dataclasses import dataclass
from typing import Any

from src.shared.errors.codes import ErrorCode


@dataclass(frozen=True, slots=True)
class AppError(Exception):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message
