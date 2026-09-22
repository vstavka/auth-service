import logging

from src.application.cache_keys import sessions_key
from src.application.dto import RefreshTokensRequest, TokenPair
from src.application.ports.cache import Cache
from src.application.ports.security import TokenService
from src.application.ports.system import Clock, UnitOfWork
from src.domain.exceptions.auth import AccountDisabledError, RefreshTokenInvalidError
from src.domain.value_objects import RefreshTokenHash

logger = logging.getLogger(__name__)


class RefreshTokensHandler:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
            token_service: TokenService,
            clock: Clock,
            cache: Cache,
    ) -> None:
        self._uow = uow
        self._token_service = token_service
        self._clock = clock
        self._cache = cache

    async def execute(self, command: RefreshTokensRequest) -> TokenPair:
        token_hash = RefreshTokenHash(
            self._token_service.hash_refresh_token(command.refresh_token),
        )
        now = self._clock.now()

        async with self._uow:
            session = await self._uow.sessions.get_by_refresh_token_hash(token_hash)
            if session is None or not session.is_active(now):
                raise RefreshTokenInvalidError()

            account = await self._uow.accounts.get_by_internal_id(session.account_id)
            if account is None:
                raise RefreshTokenInvalidError()
            if not account.is_active:
                raise AccountDisabledError()

            tokens = self._token_service.issue_tokens(
                account_id=account.public_id,
                session_id=session.public_id,
            )
            session.rotate_refresh_token(
                refresh_token_hash=RefreshTokenHash(
                    self._token_service.hash_refresh_token(tokens.refresh_token),
                ),
                expires_at=tokens.refresh_token_expires_at,
                now=now,
            )
            await self._uow.sessions.save(session)
            await self._uow.commit()

        await self._cache.delete(sessions_key(account.public_id))

        logger.info(
            "Tokens refreshed",
            extra={
                "account_id": str(account.public_id),
                "session_id": str(session.public_id),
            },
        )
        return tokens
