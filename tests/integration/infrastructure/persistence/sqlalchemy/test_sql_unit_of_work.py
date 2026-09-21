import random
from datetime import datetime, UTC

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.domain.entities.account import Account
from src.domain.enums.account_status import AccountStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.domain.value_objects.user_id import UserId
from src.infrastructure.persistence.sqlalchemy.models.account import Account as AccountORM
from src.infrastructure.persistence.sqlalchemy.sql_unit_of_work import SQLUnitOfWork


def make_account(email: str = "user@example.com") -> Account:
    now = datetime.now(UTC)
    return Account(
        id=random.randint(1, 100),
        public_id=UserId(uuid7()),
        email=Email(email),
        password_hash=PasswordHash("hashed-value"),
        status=AccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def uow_factory(session_factory):
    def factory() -> SQLUnitOfWork:
        uow = SQLUnitOfWork(session_factory)
        return uow

    return factory


class TestCommitOnSuccess:
    @pytest.mark.asyncio
    async def test_data_is_persisted_after_successful_block(
            self, uow_factory, async_engine
    ):
        account = make_account(email="commit@example.com")

        async with uow_factory() as uow:
            await uow.accounts.add(account)

        async with AsyncSession(async_engine) as verify_session:
            result = await verify_session.execute(
                select(AccountORM).where(AccountORM.email == "commit@example.com")
            )
            assert result.scalar_one_or_none() is not None


class TestRollbackOnException:
    @pytest.mark.asyncio
    async def test_data_is_not_persisted_when_exception_raised(
            self, uow_factory, async_engine
    ):
        account = make_account(email="rollback@example.com")

        with pytest.raises(ValueError):
            async with uow_factory() as uow:
                await uow.accounts.add(account)
                raise ValueError("simulated failure")

        async with AsyncSession(async_engine) as verify_session:
            result = await verify_session.execute(
                select(AccountORM).where(AccountORM.email == "rollback@example.com")
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_exception_propagates_out_of_context_manager(self, uow_factory):
        with pytest.raises(ValueError):
            async with uow_factory() as uow:
                raise ValueError("simulated failure")


class TestSessionLifecycle:
    @pytest.mark.asyncio
    async def test_session_is_closed_after_successful_block(self, uow_factory):
        async with uow_factory() as uow:
            session = uow._session
            await uow.accounts.add(make_account(email="closed@example.com"))

        assert uow._session is None

    @pytest.mark.asyncio
    async def test_session_is_closed_after_exception(self, uow_factory):
        with pytest.raises(ValueError):
            async with uow_factory() as uow:
                session = uow._session
                raise ValueError("simulated failure")

        assert uow._session is None

    @pytest.mark.asyncio
    async def test_begin_twice_raises_runtime_error(self, uow_factory):
        """
        как обсуждалось в ревью SQLUnitOfWork.
        """
        uow = uow_factory()
        await uow.begin()
        with pytest.raises(RuntimeError):
            await uow.begin()
        await uow.rollback()
        await uow._session.close()
