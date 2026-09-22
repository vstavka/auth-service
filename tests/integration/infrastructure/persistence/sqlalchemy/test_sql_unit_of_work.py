import random
from datetime import datetime, UTC
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.domain.entities.account import Account
from src.domain.enums.account_status import AccountStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password_hash import PasswordHash
from src.domain.value_objects.user_id import UserId
from src.application.dto import IntegrationEvent
from src.infrastructure.persistence.sqlalchemy.models.account import Account as AccountORM
from src.infrastructure.persistence.sqlalchemy.models.outbox_message import OutboxMessageModel
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

    @pytest.mark.asyncio
    async def test_reenter_after_successful_exit_creates_new_session(self, uow_factory):
        uow = uow_factory()

        async with uow:
            first_session = uow._session

        async with uow:
            second_session = uow._session

        assert first_session is not None
        assert second_session is not None
        assert first_session is not second_session

    @pytest.mark.asyncio
    async def test_explicit_commit_after_begin_persists(self, uow_factory, async_engine):
        account = make_account(email="explicit-commit@example.com")
        uow = uow_factory()

        await uow.begin()
        await uow.accounts.add(account)
        await uow.commit()
        await uow._session.close()
        uow._session = None

        async with AsyncSession(async_engine) as verify_session:
            result = await verify_session.execute(
                select(AccountORM).where(
                    AccountORM.email == "explicit-commit@example.com"
                )
            )
            assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_explicit_rollback_after_begin_discards_add(
            self, uow_factory, async_engine
    ):
        account = make_account(email="explicit-rollback@example.com")
        uow = uow_factory()

        await uow.begin()
        await uow.accounts.add(account)
        await uow.rollback()
        await uow._session.close()
        uow._session = None

        async with AsyncSession(async_engine) as verify_session:
            result = await verify_session.execute(
                select(AccountORM).where(
                    AccountORM.email == "explicit-rollback@example.com"
                )
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_outbox_is_sql_outbox_repository_after_begin(self, uow_factory):
        from src.infrastructure.persistence.sqlalchemy.repositories.sql_outbox_repository import (
            SQLOutboxRepository,
        )

        uow = uow_factory()
        await uow.begin()
        try:
            assert isinstance(uow.outbox, SQLOutboxRepository)
        finally:
            await uow.rollback()
            await uow._session.close()
            uow._session = None

    @pytest.mark.asyncio
    async def test_accounts_is_sql_account_repository_after_begin(self, uow_factory):
        from src.infrastructure.persistence.sqlalchemy.repositories.sql_account_repository import (
            SQLAccountRepository,
        )

        uow = uow_factory()
        await uow.begin()
        try:
            assert isinstance(uow.accounts, SQLAccountRepository)
        finally:
            await uow.rollback()
            await uow._session.close()
            uow._session = None


class TestOutboxInUnitOfWork:
    @pytest.mark.asyncio
    async def test_outbox_event_is_persisted_after_successful_block(
            self, uow_factory, async_engine
    ):
        event = IntegrationEvent(
            event_id=uuid4(),
            event_type="identity.account.registered",
            aggregate_id="agg-1",
            occurred_at=datetime.now(UTC),
            payload={"account_id": "agg-1"},
        )

        async with uow_factory() as uow:
            await uow.outbox.add(event)

        async with AsyncSession(async_engine) as verify_session:
            result = await verify_session.execute(
                select(OutboxMessageModel).where(OutboxMessageModel.id == str(event.event_id))
            )
            assert result.scalar_one_or_none() is not None
