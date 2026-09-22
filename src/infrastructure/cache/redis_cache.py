from __future__ import annotations

from datetime import timedelta

from redis.asyncio import Redis

from src.application.ports.cache import Cache


class RedisCache(Cache):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> bytes | None:
        return await self._redis.get(key)

    async def set(
        self,
        key: str,
        value: bytes,
        *,
        ttl: timedelta | None = None,
    ) -> None:
        await self._redis.set(
            name=key,
            value=value,
            ex=ttl,
        )

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def delete_many(self, keys: list[str]) -> None:
        if keys:
            await self._redis.delete(*keys)

    async def aclose(self) -> None:
        await self._redis.aclose()