from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid6 import uuid7

from src.domain.entities import Account, Session
from src.domain.enums import AccountStatus
from src.domain.value_objects import Email, PasswordHash, RefreshTokenHash, SessionId, UserId
from src.infrastructure.persistence.sqlalchemy.repositories.sql_account_repository import (
    SQLAccountRepository,
)
from src.infrastructure.persistence.sqlalchemy.repositories.sql_session_repository import (
    SQLSessionRepository,
)


def make_account(email: str = "session-owner@example.com") -> Account:
    now = datetime.now(UTC)
    return Account(
        id=None,
        public_id=UserId(uuid7()),
        email=Email(email),
        password_hash=PasswordHash("hashed-value"),
        status=AccountStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


def make_session(*, account_id: int, token_hash: str = "a" * 64) -> Session:
    now = datetime.now(UTC)
    return Session.create(
        public_id=SessionId(uuid7()),
        account_id=account_id,
        refresh_token_hash=RefreshTokenHash(token_hash),
        now=now,
        expires_at=now + timedelta(days=7),
        ip="203.0.113.10",
        user_agent="Mozilla/5.0",
        device_info="Chrome",
    )


@pytest.fixture
def account_repository(session: AsyncSession) -> SQLAccountRepository:
    return SQLAccountRepository(session)


@pytest.fixture
def session_repository(session: AsyncSession) -> SQLSessionRepository:
    return SQLSessionRepository(session)


class TestSQLSessionRepository:
    @pytest.mark.asyncio
    async def test_add_persists_session_and_assigns_id(
            self,
            account_repository: SQLAccountRepository,
            session_repository: SQLSessionRepository,
    ):
        account = make_account()
        await account_repository.add(account)
        session = make_session(account_id=account.id)

        await session_repository.add(session)

        assert session.id is not None
        fetched = await session_repository.get_by_public_id(session.public_id)
        assert fetched is not None
        assert fetched.account_id == account.id
        assert fetched.refresh_token_hash == session.refresh_token_hash
        assert fetched.ip == "203.0.113.10"

    @pytest.mark.asyncio
    async def test_get_by_public_id_returns_none_when_missing(
            self,
            session_repository: SQLSessionRepository,
    ):
        result = await session_repository.get_by_public_id(SessionId(uuid7()))
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_refresh_token_hash(
            self,
            account_repository: SQLAccountRepository,
            session_repository: SQLSessionRepository,
    ):
        account = make_account(email="hash-owner@example.com")
        await account_repository.add(account)
        token_hash = "b" * 64
        session = make_session(account_id=account.id, token_hash=token_hash)
        await session_repository.add(session)

        fetched = await session_repository.get_by_refresh_token_hash(
            RefreshTokenHash(token_hash),
        )

        assert fetched is not None
        assert fetched.public_id == session.public_id

    @pytest.mark.asyncio
    async def test_get_by_refresh_token_hash_returns_none_when_missing(
            self,
            session_repository: SQLSessionRepository,
    ):
        result = await session_repository.get_by_refresh_token_hash(
            RefreshTokenHash("d" * 64),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_account_id(
            self,
            account_repository: SQLAccountRepository,
            session_repository: SQLSessionRepository,
    ):
        first_account = make_account(email="first-owner@example.com")
        second_account = make_account(email="second-owner@example.com")
        await account_repository.add(first_account)
        await account_repository.add(second_account)

        first_session = make_session(account_id=first_account.id, token_hash="e" * 64)
        second_session = make_session(account_id=first_account.id, token_hash="f" * 64)
        other_session = make_session(account_id=second_account.id, token_hash="1" * 64)
        await session_repository.add(first_session)
        await session_repository.add(second_session)
        await session_repository.add(other_session)

        sessions = await session_repository.list_by_account_id(first_account.id)

        assert {item.public_id for item in sessions} == {
            first_session.public_id,
            second_session.public_id,
        }

    @pytest.mark.asyncio
    async def test_save_persists_revoked_at(
            self,
            account_repository: SQLAccountRepository,
            session_repository: SQLSessionRepository,
    ):
        account = make_account(email="revoke-save@example.com")
        await account_repository.add(account)
        session = make_session(account_id=account.id, token_hash="2" * 64)
        await session_repository.add(session)
        revoked_at = datetime.now(UTC)
        session.revoke(revoked_at)

        await session_repository.save(session)

        fetched = await session_repository.get_by_public_id(session.public_id)
        assert fetched is not None
        assert fetched.revoked_at is not None
        assert fetched.is_revoked is True
