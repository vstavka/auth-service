import logging

from src.application.cache_keys import sessions_key
from src.application.dto import RevokeSessionRequest
from src.application.ports.cache import Cache
from src.application.ports.system import Clock, UnitOfWork
from src.application.services import require_active_account
from src.domain.exceptions.auth import SessionNotFoundError

logger = logging.getLogger(__name__)


class RevokeSessionHandler:
    def __init__(self, *, uow: UnitOfWork, clock: Clock, cache: Cache) -> None:
        self._uow = uow
        self._clock = clock
        self._cache = cache

    async def execute(self, command: RevokeSessionRequest) -> None:
        async with self._uow:
            account = await require_active_account(self._uow, command.actor_id)
            session = await self._uow.sessions.get_by_public_id(command.session_id)
            if session is None or session.account_id != account.id:
                raise SessionNotFoundError()

            session.revoke(self._clock.now())
            await self._uow.sessions.save(session)
            await self._uow.commit()

        await self._cache.delete(sessions_key(account.public_id))

        logger.info(
            "Session revoked",
            extra={
                "account_id": str(account.public_id),
                "session_id": str(command.session_id),
            },
        )
