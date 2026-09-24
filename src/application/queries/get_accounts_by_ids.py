import json
from datetime import timedelta

from src.application.cache_keys import account_key
from src.application.dto import AccountPublic, GetAccountsByIdsQuery, account_to_public
from src.application.ports.cache import Cache
from src.application.ports.system import UnitOfWork
from src.domain.value_objects import UserId


class GetAccountsByIdsHandler:
    def __init__(self, *, uow: UnitOfWork, cache: Cache, ttl: timedelta) -> None:
        self._uow = uow
        self._cache = cache
        self._ttl = ttl

    async def execute(self, query: GetAccountsByIdsQuery) -> list[AccountPublic]:
        if not query.account_ids:
            return []

        unique_ids = list(dict.fromkeys(query.account_ids))
        results_by_id: dict[UserId, AccountPublic] = {}
        missing: list[UserId] = []

        for account_id in unique_ids:
            key = account_key(account_id)
            raw: bytes | None = await self._cache.get(key)
            if raw is None:
                missing.append(account_id)
                continue
            try:
                payload = json.loads(raw)
                results_by_id[account_id] = AccountPublic.from_dict(payload)
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                missing.append(account_id)

        if missing:
            async with self._uow:
                accounts = await self._uow.accounts.get_by_ids(missing)

            for account in accounts:
                public = account_to_public(account)
                results_by_id[account.public_id] = public
                payload: bytes = json.dumps(
                    public.to_dict(),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                await self._cache.set(
                    account_key(account.public_id),
                    payload,
                    ttl=self._ttl,
                )

        return [
            results_by_id[account_id]
            for account_id in unique_ids
            if account_id in results_by_id
        ]
