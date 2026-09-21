from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str

    def __str__(self):
        return str(self.value)
