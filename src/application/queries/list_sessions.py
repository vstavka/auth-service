import json
from datetime import timedelta

from src.application.cache_keys import sessions_key
from src.application.dto import ListSessionsQuery, SessionPublic, session_to_public
from src.application.ports.cache import Cache
from src.application.ports.system import UnitOfWork
from src.application.services import require_active_account


class ListSessionsHandler:
    def __init__(self, *, uow: UnitOfWork, cache: Cache, ttl: timedelta) -> None:
        self._uow = uow
        self._cache = cache
        self._ttl = ttl

    async def execute(self, query: ListSessionsQuery) -> list[SessionPublic]:
        key = sessions_key(query.actor_id)
        raw: bytes | None = await self._cache.get(key)
        if raw is not None:
            try:
                payload = json.loads(raw)
                return [
                    SessionPublic.from_dict(item)
                    for item in payload
                ]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        async with self._uow:
            account = await require_active_account(self._uow, query.actor_id)
            sessions = await self._uow.sessions.list_by_account_id(account.id)
        results = [session_to_public(session) for session in sessions]
        payload: bytes = (json.dumps([row.to_dict() for row in results], ensure_ascii=False, separators=(",", ":"))
                          .encode("utf-8"))
        await self._cache.set(
            key,
            payload,
            ttl=self._ttl,
        )
        return results
