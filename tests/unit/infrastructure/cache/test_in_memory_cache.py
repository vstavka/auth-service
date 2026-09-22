from datetime import timedelta

import pytest

from src.infrastructure.cache import InMemoryCache


@pytest.mark.asyncio
class TestInMemoryCache:
    async def test_set_and_get(self) -> None:
        cache = InMemoryCache()
        await cache.set("k", b"v")
        assert await cache.get("k") == b"v"

    async def test_missing_key_returns_none(self) -> None:
        cache = InMemoryCache()
        assert await cache.get("missing") is None

    async def test_expired_key_is_removed(self) -> None:
        cache = InMemoryCache()
        await cache.set("k", b"v", ttl=timedelta(seconds=-1))
        assert await cache.get("k") is None

    async def test_delete(self) -> None:
        cache = InMemoryCache()
        await cache.set("k", b"v")
        await cache.delete("k")
        assert await cache.get("k") is None

    async def test_delete_many(self) -> None:
        cache = InMemoryCache()
        await cache.set("a", b"1")
        await cache.set("b", b"2")
        await cache.set("c", b"3")
        await cache.delete_many(["a", "c"])
        assert await cache.get("a") is None
        assert await cache.get("b") == b"2"
        assert await cache.get("c") is None

    async def test_overwrite(self) -> None:
        cache = InMemoryCache()
        await cache.set("k", b"old")
        await cache.set("k", b"new")
        assert await cache.get("k") == b"new"
