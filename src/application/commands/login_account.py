import logging

from src.application.cache_keys import sessions_key
from src.application.dto import LoginRequest, TokenPair
from src.application.ports.cache import Cache
from src.application.ports.security import PasswordHasher, TokenService
from src.application.ports.system import Clock, IdGenerator, UnitOfWork
from src.application.services import issue_session
from src.domain.exceptions.auth import AccountDisabledError, InvalidCredentialsError
from src.domain.value_objects import Email

logger = logging.getLogger(__name__)


class LoginAccountHandler:
    def __init__(
            self,
            *,
            uow: UnitOfWork,
            password_hasher: PasswordHasher,
            token_service: TokenService,
            id_generator: IdGenerator,
            clock: Clock,
            cache: Cache,
    ) -> None:
        self._uow = uow
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._id_generator = id_generator
        self._clock = clock
        self._cache = cache

    async def execute(self, command: LoginRequest) -> TokenPair:
        email = Email(command.email)

        async with self._uow:
            account = await self._uow.accounts.get_by_email(email)
            if account is None or not self._password_hasher.verify(
                    command.password,
                    account.password_hash,
            ):
                logger.warning("Login rejected: invalid credentials")
                raise InvalidCredentialsError()

            if not account.is_active:
                logger.warning(
                    "Login rejected: account disabled",
                    extra={"account_id": str(account.public_id)},
                )
                raise AccountDisabledError()

            tokens = await issue_session(
                uow=self._uow,
                token_service=self._token_service,
                id_generator=self._id_generator,
                clock=self._clock,
                account=account,
                ip=command.ip,
                user_agent=command.user_agent,
                device_info=command.device_info,
            )
            await self._uow.commit()

        await self._cache.delete(sessions_key(account.public_id))

        logger.info(
            "Account logged in",
            extra={"account_id": str(account.public_id)},
        )
        return tokens
