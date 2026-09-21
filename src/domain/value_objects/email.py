from dataclasses import dataclass

from email_validator import validate_email, EmailNotValidError

from src.domain.exceptions.email import InvalidEmailError


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        try:
            validated = validate_email(
                self.value.lower(),
                check_deliverability=False,
            )
        except EmailNotValidError as exc:
            raise InvalidEmailError(str(exc))

        object.__setattr__(self, "value", validated.normalized)

    def __str__(self) -> str:
        return self.value
