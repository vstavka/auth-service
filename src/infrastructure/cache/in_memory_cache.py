from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.application.ports.cache import Cache


class InMemoryCache(Cache):
    def __init__(self) -> None:
        self._items: dict[str, tuple[bytes, datetime | None]] = {}

    async def get(self, key: str) -> bytes | None:
        item = self._items.get(key)
        if item is None:
            return None

        value, expires_at = item

        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            self._items.pop(key, None)
            return None

        return value

    async def set(
        self,
        key: str,
        value: bytes,
        *,
        ttl: timedelta | None = None,
    ) -> None:
        expires_at = (
            datetime.now(timezone.utc) + ttl
            if ttl is not None
            else None
        )
        self._items[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._items.pop(key, None)

    async def delete_many(self, keys: list[str]) -> None:
        for key in keys:
            self._items.pop(key, None)