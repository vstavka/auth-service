from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RefreshTokenHash:
    value: str

    def __str__(self):
        return str(self.value)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("RefreshTokenHash.value must be str")

        if not self.value:
            raise ValueError("RefreshTokenHash.value must not be empty")
