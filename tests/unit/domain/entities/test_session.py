from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId

SESSION_ID = 10
ACCOUNT_ID = 1
SESSION_PUBLIC_ID = SessionId(
    value=UUID("22345678-1234-5678-1234-567812345678")
)
REFRESH_TOKEN_HASH = RefreshTokenHash("a" * 64)
CREATED_AT = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
EXPIRES_AT = CREATED_AT + timedelta(days=7)
IP = "203.0.113.10"
USER_AGENT = "Mozilla/5.0"
DEVICE_INFO = "Chrome on Windows"


@pytest.fixture
def session() -> Session:
    return Session.create(
        id=SESSION_ID,
        public_id=SESSION_PUBLIC_ID,
        account_id=ACCOUNT_ID,
        refresh_token_hash=REFRESH_TOKEN_HASH,
        now=CREATED_AT,
        expires_at=EXPIRES_AT,
        ip=IP,
        user_agent=USER_AGENT,
        device_info=DEVICE_INFO,
    )


@pytest.mark.unit
class TestSession:
    def test_create_session(self, session: Session):
        assert session.id == SESSION_ID
        assert session.public_id == SESSION_PUBLIC_ID
        assert session.account_id == ACCOUNT_ID
        assert session.refresh_token_hash == REFRESH_TOKEN_HASH
        assert session.ip == IP
        assert session.user_agent == USER_AGENT
        assert session.device_info == DEVICE_INFO
        assert session.created_at == CREATED_AT
        assert session.expires_at == EXPIRES_AT
        assert session.revoked_at is None
        assert session.is_revoked is False
        assert session.is_expired(CREATED_AT) is False
        assert session.is_active(CREATED_AT) is True

    def test_create_without_id_sets_id_to_none(self):
        session = Session.create(
            public_id=SESSION_PUBLIC_ID,
            account_id=ACCOUNT_ID,
            refresh_token_hash=REFRESH_TOKEN_HASH,
            now=CREATED_AT,
            expires_at=EXPIRES_AT,
        )

        assert session.id is None
        assert session.ip is None
        assert session.user_agent is None
        assert session.device_info is None
        assert session.revoked_at is None
        assert session.is_active(CREATED_AT) is True

    def test_create_rejects_expires_at_not_after_created_at(self):
        with pytest.raises(ValueError, match="expires_at must be greater than created_at"):
            Session.create(
                public_id=SESSION_PUBLIC_ID,
                account_id=ACCOUNT_ID,
                refresh_token_hash=REFRESH_TOKEN_HASH,
                now=CREATED_AT,
                expires_at=CREATED_AT,
            )

    def test_revoke_sets_revoked_at_and_is_inactive(self, session: Session):
        revoked_at = datetime(2026, 9, 15, 18, 5, tzinfo=timezone.utc)

        session.revoke(revoked_at)

        assert session.revoked_at == revoked_at
        assert session.is_revoked is True
        assert session.is_active(revoked_at) is False

    def test_revoking_twice_does_not_change_revoked_at(self, session: Session):
        first_revoked_at = datetime(2026, 9, 15, 18, 5, tzinfo=timezone.utc)
        second_revoked_at = datetime(2026, 9, 15, 18, 10, tzinfo=timezone.utc)

        session.revoke(first_revoked_at)
        session.revoke(second_revoked_at)

        assert session.revoked_at == first_revoked_at
        assert session.is_revoked is True

    def test_is_expired_false_before_expires_at(self, session: Session):
        now = EXPIRES_AT - timedelta(seconds=1)

        assert session.is_expired(now) is False
        assert session.is_active(now) is True

    def test_is_expired_true_at_expires_at(self, session: Session):
        assert session.is_expired(EXPIRES_AT) is True
        assert session.is_active(EXPIRES_AT) is False

    def test_rotate_refresh_token_updates_hash_and_expiry(self, session: Session):
        now = datetime(2026, 9, 16, 18, 0, tzinfo=timezone.utc)
        new_hash = RefreshTokenHash("b" * 64)
        new_expires_at = now + timedelta(days=7)

        session.rotate_refresh_token(
            refresh_token_hash=new_hash,
            expires_at=new_expires_at,
            now=now,
        )

        assert session.refresh_token_hash == new_hash
        assert session.expires_at == new_expires_at
        assert session.public_id == SESSION_PUBLIC_ID
        assert session.created_at == CREATED_AT
        assert session.is_active(now) is True

    def test_rotate_refresh_token_rejects_expires_at_not_after_now(self, session: Session):
        with pytest.raises(ValueError, match="expires_at must be greater than now"):
            session.rotate_refresh_token(
                refresh_token_hash=RefreshTokenHash("b" * 64),
                expires_at=CREATED_AT,
                now=CREATED_AT,
            )
