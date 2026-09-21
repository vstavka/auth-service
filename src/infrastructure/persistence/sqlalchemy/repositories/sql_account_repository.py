import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.application.ports.repositories import AccountRepository
from src.domain.entities import Account
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.value_objects import Email, UserId
from src.infrastructure.persistence.sqlalchemy.mappers.account import account_domain_to_orm, account_orm_to_domain
from src.infrastructure.persistence.sqlalchemy.models import Account as AccountORM

logger = logging.getLogger(__name__)


class SQLAccountRepository(AccountRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, account: Account) -> None:
        """Добавляет новый аккаунт в текущую транзакцию."""
        logger.debug("Adding account email=%s public_id=%s", account.email, account.public_id)
        account_orm = account_domain_to_orm(account)
        self._session.add(account_orm)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            logger.info(
                "Account with email=%s already exists, integrity constraint violated",
                account.email,
            )
            raise EmailAlreadyRegisteredError(
                details={"email": account.email.value},
            ) from exc
        except Exception:
            logger.error(
                "Unexpected error while adding account email=%s", account.email, exc_info=True
            )
            raise
        account.id = account_orm.id
        logger.debug("Account added successfully email=%s", account.email)

    async def get_by_id(self, account_id: UserId) -> Account | None:
        """Возвращает аккаунт по идентификатору."""
        account_id_value = str(account_id.value)
        logger.debug("Fetching account by id=%s", account_id_value)
        stmt = select(AccountORM).where(AccountORM.public_id == account_id_value)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            logger.debug("Account not found id=%s", account_id_value)
            return None
        return account_orm_to_domain(entity)

    async def get_by_email(self, email: Email) -> Account | None:
        """Возвращает аккаунт по нормализованному email."""
        logger.debug("Fetching account by email=%s", email.value)
        stmt = select(AccountORM).where(AccountORM.email == email.value)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            logger.debug("Account not found email=%s", email.value)
            return None
        return account_orm_to_domain(entity)

    async def get_by_internal_id(self, account_id: int) -> Account | None:
        """Возвращает аккаунт по внутреннему числовому идентификатору."""
        logger.debug("Fetching account by internal id=%s", account_id)
        stmt = select(AccountORM).where(AccountORM.id == account_id)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            logger.debug("Account not found internal id=%s", account_id)
            return None
        return account_orm_to_domain(entity)

    async def save(self, account: Account) -> None:
        """Сохраняет изменения существующего аккаунта."""
        if account.id is None:
            raise RuntimeError("Cannot save account without id")

        logger.debug("Saving account id=%s", account.id)
        stmt = select(AccountORM).where(AccountORM.id == account.id)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity is None:
            raise RuntimeError(f"Account id={account.id} not found")

        entity.email = account.email.value
        entity.status = account.status
        entity.password_hash = account.password_hash.value
        entity.updated_at = account.updated_at
        try:
            await self._session.flush()
        except IntegrityError as exc:
            logger.info(
                "Account with email=%s already exists, integrity constraint violated",
                account.email,
            )
            raise EmailAlreadyRegisteredError(
                details={"email": account.email.value},
            ) from exc
