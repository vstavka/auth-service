from __future__ import annotations

from datetime import timedelta
from typing import Protocol


class Cache(Protocol):
    async def get(self, key: str) -> bytes | None:
        ...

    async def set(
            self,
            key: str,
            value: bytes,
            *,
            ttl: timedelta | None = None,
    ) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def delete_many(self, keys: list[str]) -> None:
        ...
