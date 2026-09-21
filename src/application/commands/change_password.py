import logging

from src.application.dto import ChangePasswordRequest
from src.application.ports.security import PasswordHasher
from src.application.ports.system import Clock, UnitOfWork
from src.application.services import require_active_account
from src.domain.exceptions.auth import InvalidCredentialsError, SessionNotFoundError
from src.domain.services.password_policy import PasswordPolicy

logger = logging.getLogger(__name__)


class ChangePasswordHandler:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
            password_policy: PasswordPolicy,
            password_hasher: PasswordHasher,
            clock: Clock,
    ) -> None:
        self._uow = uow
        self._password_policy = password_policy
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(self, command: ChangePasswordRequest) -> None:
        self._password_policy.validate(command.new_password)

        async with self._uow:
            account = await require_active_account(self._uow, command.actor_id)
            if not self._password_hasher.verify(
                    command.current_password,
                    account.password_hash,
            ):
                raise InvalidCredentialsError()

            current_session = await self._uow.sessions.get_by_public_id(
                command.current_session_id,
            )
            if current_session is None or current_session.account_id != account.id:
                raise SessionNotFoundError()

            now = self._clock.now()
            account.change_password(
                new_password_hash=self._password_hasher.hash(command.new_password),
                now=now,
            )
            await self._uow.accounts.save(account)

            for session in await self._uow.sessions.list_by_account_id(account.id):
                if session.public_id == current_session.public_id:
                    continue
                session.revoke(now)
                await self._uow.sessions.save(session)

            await self._uow.commit()

        logger.info(
            "Account password changed",
            extra={"account_id": str(account.public_id)},
        )
