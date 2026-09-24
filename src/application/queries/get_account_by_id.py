import json
from datetime import timedelta

from src.application.cache_keys import account_key
from src.application.dto import AccountPublic, GetAccountByIdQuery, account_to_public
from src.application.ports.cache import Cache
from src.application.ports.system import UnitOfWork
from src.domain.exceptions.auth import UserNotFoundError


class GetAccountByIdHandler:
    def __init__(self, *, uow: UnitOfWork, cache: Cache, ttl: timedelta) -> None:
        self._uow = uow
        self._cache = cache
        self._ttl = ttl

    async def execute(self, query: GetAccountByIdQuery) -> AccountPublic:
        key = account_key(query.account_id)
        raw: bytes | None = await self._cache.get(key)
        if raw is not None:
            try:
                payload = json.loads(raw)
                return AccountPublic.from_dict(payload)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass

        async with self._uow:
            account = await self._uow.accounts.get_by_id(query.account_id)

        if account is None:
            raise UserNotFoundError(details={"account_id": str(query.account_id.value)})

        result = account_to_public(account)
        payload: bytes = json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        await self._cache.set(key, payload, ttl=self._ttl)
        return result
