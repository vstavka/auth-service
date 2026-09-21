import logging

from src.application.dto import ChangeEmailRequest, AccountPublic, account_to_public
from src.application.ports.system import Clock, UnitOfWork
from src.application.services import require_active_account
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.value_objects import Email

logger = logging.getLogger(__name__)


class ChangeEmailHandler:
    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangeEmailRequest) -> AccountPublic:
        email = Email(command.email)

        async with self._uow:
            account = await require_active_account(self._uow, command.actor_id)
            existing = await self._uow.accounts.get_by_email(email)
            if existing is not None and existing.public_id != account.public_id:
                raise EmailAlreadyRegisteredError(details={"email": email.value})

            account.change_email(email=email, now=self._clock.now())
            await self._uow.accounts.save(account)
            await self._uow.commit()

        logger.info(
            "Account email changed",
            extra={"account_id": str(account.public_id)},
        )
        return account_to_public(account)
