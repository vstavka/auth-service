from dataclasses import dataclass

from src.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class GetMeQuery:
    actor_id: UserId
