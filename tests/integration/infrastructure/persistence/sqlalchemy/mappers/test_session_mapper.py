from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from uuid6 import uuid7

from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId
from src.infrastructure.persistence.sqlalchemy.mappers.session import (
    session_domain_to_orm,
    session_orm_to_domain,
)
from src.infrastructure.persistence.sqlalchemy.models.session import Session as SessionORM


@pytest.fixture
def domain_session() -> Session:
    now = datetime.now(UTC)
    return Session(
        id=1,
        public_id=SessionId(uuid7()),
        account_id=1,
        refresh_token_hash=RefreshTokenHash("a" * 64),
        ip="203.0.113.10",
        user_agent="Mozilla/5.0",
        device_info="Chrome",
        created_at=now,
        expires_at=now + timedelta(days=7),
        revoked_at=None,
    )


class TestSessionDomainToOrm:
    def test_maps_all_fields(self, domain_session: Session):
        orm_session = session_domain_to_orm(domain_session)

        assert isinstance(orm_session, SessionORM)
        assert orm_session.public_id == str(domain_session.public_id.value)
        assert orm_session.account_id == domain_session.account_id
        assert orm_session.refresh_token_hash == domain_session.refresh_token_hash.value
        assert orm_session.ip == domain_session.ip
        assert orm_session.user_agent == domain_session.user_agent
        assert orm_session.device_info == domain_session.device_info
        assert orm_session.created_at == domain_session.created_at
        assert orm_session.expires_at == domain_session.expires_at
        assert orm_session.revoked_at is None

    def test_does_not_set_internal_int_id(self, domain_session: Session):
        orm_session = session_domain_to_orm(domain_session)
        assert orm_session.id is None


class TestSessionOrmToDomain:
    def test_maps_all_fields(self):
        now = datetime.now(UTC)
        public_id = uuid4()
        revoked_at = now + timedelta(hours=1)
        orm_session = SessionORM(
            id=1,
            public_id=public_id,
            account_id=2,
            refresh_token_hash="b" * 64,
            ip=None,
            user_agent=None,
            device_info=None,
            created_at=now,
            expires_at=now + timedelta(days=7),
            revoked_at=revoked_at,
        )

        session = session_orm_to_domain(orm_session)

        assert session.id == 1
        assert session.public_id.value == public_id
        assert session.account_id == 2
        assert session.refresh_token_hash.value == "b" * 64
        assert session.ip is None
        assert session.revoked_at == revoked_at

    def test_orm_to_domain_accepts_public_id_as_str(self):
        now = datetime.now(UTC)
        public_id = uuid4()
        orm_session = SessionORM(
            id=1,
            public_id=str(public_id),
            account_id=1,
            refresh_token_hash="c" * 64,
            ip=None,
            user_agent=None,
            device_info=None,
            created_at=now,
            expires_at=now + timedelta(days=7),
            revoked_at=None,
        )

        session = session_orm_to_domain(orm_session)

        assert session.public_id.value == public_id
        assert isinstance(session.public_id.value, UUID)

    def test_orm_to_domain_attaches_utc_to_naive_datetimes(self):
        naive_now = datetime(2026, 9, 21, 12, 0, 0)
        orm_session = SessionORM(
            id=1,
            public_id=str(uuid4()),
            account_id=1,
            refresh_token_hash="d" * 64,
            ip=None,
            user_agent=None,
            device_info=None,
            created_at=naive_now,
            expires_at=naive_now + timedelta(days=7),
            revoked_at=naive_now + timedelta(hours=1),
        )

        session = session_orm_to_domain(orm_session)

        assert session.created_at.tzinfo is not None
        assert session.expires_at.tzinfo is not None
        assert session.revoked_at is not None
        assert session.revoked_at.tzinfo is not None
