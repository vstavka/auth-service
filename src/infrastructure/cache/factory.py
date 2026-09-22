from __future__ import annotations

import logging

from src.application.ports.cache import Cache
from src.infrastructure.cache.in_memory_cache import InMemoryCache
from src.infrastructure.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)


def create_cache(*, backend: str, redis_url: str) -> Cache:
    if backend == "redis":
        from redis.asyncio import Redis

        logger.info("Using Redis cache")
        return RedisCache(Redis.from_url(redis_url, decode_responses=False))
    logger.info("Using in-memory cache")
    return InMemoryCache()
