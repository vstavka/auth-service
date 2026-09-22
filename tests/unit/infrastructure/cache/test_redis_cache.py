from datetime import timedelta

import pytest

from src.infrastructure.cache import RedisCache


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}
        self.closed = False

    async def get(self, key: str) -> bytes | None:
        return self.store.get(key)

    async def set(self, name: str, value: bytes, ex: timedelta | None = None) -> None:
        self.store[name] = value
        self.last_ex = ex

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self.store.pop(key, None)

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
class TestRedisCache:
    async def test_get_set_delete(self) -> None:
        redis = FakeRedis()
        cache = RedisCache(redis)  # type: ignore[arg-type]
        await cache.set("k", b"v", ttl=timedelta(seconds=5))
        assert await cache.get("k") == b"v"
        assert redis.last_ex == timedelta(seconds=5)
        await cache.delete("k")
        assert await cache.get("k") is None

    async def test_delete_many_skips_empty(self) -> None:
        redis = FakeRedis()
        cache = RedisCache(redis)  # type: ignore[arg-type]
        await cache.set("a", b"1")
        await cache.delete_many([])
        assert await cache.get("a") == b"1"
        await cache.delete_many(["a"])
        assert await cache.get("a") is None

    async def test_aclose(self) -> None:
        redis = FakeRedis()
        cache = RedisCache(redis)  # type: ignore[arg-type]
        await cache.aclose()
        assert redis.closed is True
