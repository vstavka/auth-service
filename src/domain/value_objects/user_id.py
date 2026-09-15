from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserId:
    value: UUID

    def __str__(self):
        return str(self.value)

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise TypeError("UserId.value must be UUID")
