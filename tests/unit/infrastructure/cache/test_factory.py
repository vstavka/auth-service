from src.infrastructure.cache.factory import create_cache
from src.infrastructure.cache.in_memory_cache import InMemoryCache
from src.infrastructure.cache.redis_cache import RedisCache


def test_create_cache_memory() -> None:
    cache = create_cache(backend="memory", redis_url="redis://localhost:6379/0")
    assert isinstance(cache, InMemoryCache)


async def test_create_cache_redis() -> None:
    cache = create_cache(backend="redis", redis_url="redis://localhost:6379/0")
    assert isinstance(cache, RedisCache)
    await cache.aclose()
