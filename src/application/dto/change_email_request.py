from dataclasses import dataclass

from src.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class ChangeEmailRequest:
    actor_id: UserId
    email: str
