from uuid import UUID

from src.application.cache_keys import account_key, sessions_key
from src.domain.value_objects import UserId

ACTOR_ID = UserId(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"))


def test_account_key() -> None:
    assert account_key(ACTOR_ID) == f"auth:accounts:{ACTOR_ID}"
    assert account_key(ACTOR_ID.value) == f"auth:accounts:{ACTOR_ID.value}"


def test_sessions_key() -> None:
    assert sessions_key(ACTOR_ID) == f"auth:sessions:{ACTOR_ID}"
