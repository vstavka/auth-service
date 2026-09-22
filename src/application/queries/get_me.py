import json
from datetime import timedelta

from src.application.cache_keys import account_key
from src.application.dto import AccountPublic, GetMeQuery, account_to_public
from src.application.ports.cache import Cache
from src.application.ports.system import UnitOfWork
from src.application.services import require_active_account


class GetMeHandler:
    def __init__(self, *, uow: UnitOfWork, cache: Cache, ttl: timedelta) -> None:
        self._uow = uow
        self._cache = cache
        self._ttl = ttl

    async def execute(self, query: GetMeQuery) -> AccountPublic:
        key = account_key(query.actor_id)
        raw: bytes | None = await self._cache.get(key)
        if raw is not None:
            try:
                payload = json.loads(raw)
                return AccountPublic.from_dict(payload)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        async with self._uow:
            account = await require_active_account(self._uow, query.actor_id)
        results = account_to_public(account)
        payload: bytes = json.dumps(results.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        await self._cache.set(
            key,
            payload,
            ttl=self._ttl,
        )
        return results
