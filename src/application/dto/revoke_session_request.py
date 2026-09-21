from dataclasses import dataclass

from src.domain.value_objects import SessionId, UserId


@dataclass(frozen=True, slots=True)
class RevokeSessionRequest:
    actor_id: UserId
    session_id: SessionId
