from __future__ import annotations

from uuid import UUID

from src.domain.value_objects import UserId


def account_key(account_id: UserId | UUID | str) -> str:
    return f"auth:accounts:{account_id}"


def sessions_key(account_id: UserId | UUID | str) -> str:
    return f"auth:sessions:{account_id}"
