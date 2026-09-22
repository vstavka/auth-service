import logging

from src.application.cache_keys import sessions_key
from src.application.dto import RevokeAllSessionsRequest
from src.application.ports.cache import Cache
from src.application.ports.system import Clock, UnitOfWork
from src.application.services import require_active_account

logger = logging.getLogger(__name__)


class RevokeAllSessionsHandler:
    def __init__(self, *, uow: UnitOfWork, clock: Clock, cache: Cache) -> None:
        self._uow = uow
        self._clock = clock
        self._cache = cache

    async def execute(self, command: RevokeAllSessionsRequest) -> None:
        async with self._uow:
            account = await require_active_account(self._uow, command.actor_id)
            now = self._clock.now()
            sessions = await self._uow.sessions.list_by_account_id(account.id)
            for session in sessions:
                session.revoke(now)
                await self._uow.sessions.save(session)
            await self._uow.commit()

        await self._cache.delete(sessions_key(account.public_id))

        logger.info(
            "All sessions revoked",
            extra={"account_id": str(account.public_id)},
        )
