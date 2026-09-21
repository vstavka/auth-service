from dataclasses import dataclass

from src.domain.value_objects import SessionId, UserId


@dataclass(frozen=True, slots=True)
class ChangePasswordRequest:
    actor_id: UserId
    current_password: str
    new_password: str
    current_session_id: SessionId
