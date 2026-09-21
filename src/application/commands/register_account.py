import logging
from dataclasses import dataclass

from src.application.dto import TokenPair, RegisterRequest
from src.application.ports.security import PasswordHasher, TokenService
from src.application.ports.system import Clock, IdGenerator, UnitOfWork
from src.domain.entities import Account
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.services.password_policy import PasswordPolicy
from src.domain.value_objects import Email, UserId

logger = logging.getLogger(__name__)


class RegisterAccountHandler:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
            password_policy: PasswordPolicy,
            password_hasher: PasswordHasher,
            token_service: TokenService,
            id_generator: IdGenerator,
            clock: Clock,
    ) -> None:
        self._uow = uow
        self._password_policy = password_policy
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._id_generator = id_generator
        self._clock = clock

    async def execute(
            self,
            command: RegisterRequest,
    ) -> TokenPair:
        email = Email(command.email)
        self._password_policy.validate(command.password)

        logger.info(
            "Registering account",
            extra={"email": email.value},
        )

        password_hash = self._password_hasher.hash(command.password)
        account_id = UserId(self._id_generator.new())

        async with self._uow:
            existing_account = await self._uow.accounts.get_by_email(email)

            if existing_account is not None:
                logger.warning(
                    "Registration rejected: email is already registered",
                    extra={"email": email.value},
                )
                raise EmailAlreadyRegisteredError()

            account = Account.create(
                public_id=account_id,
                email=email,
                password_hash=password_hash,
                now=self._clock.now(),
            )

            await self._uow.accounts.add(account)
            await self._uow.commit()

        logger.info(
            "Account successfully registered",
            extra={
                "account_id": str(account.public_id),
                "email": account.email.value,
            },
        )

        tokens = self._token_service.issue_tokens(account.public_id)

        logger.info(
            "Tokens issued after registration",
            extra={"account_id": str(account.public_id)},
        )

        return tokens
