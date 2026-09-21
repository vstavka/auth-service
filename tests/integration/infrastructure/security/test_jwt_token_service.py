from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.domain.exceptions.auth import AccessTokenInvalidError
from src.domain.value_objects import SessionId, UserId
from src.infrastructure.security.jwt_token_service import JWTTokenService
from src.shared.errors.codes import ErrorCode
from tests.fakes.system.fake_clock import FakeClock


@pytest.mark.asyncio
class TestJWTTokenService:
    @pytest.fixture
    def clock(self) -> FakeClock:
        return FakeClock(
            datetime.now(tz=UTC),
        )

    @pytest.fixture
    def token_service(
            self,
            clock: FakeClock,
    ) -> JWTTokenService:
        return JWTTokenService(
            secret_key="test-secret-key-that-is-long-enough-for-tests",
            clock=clock,
            access_token_ttl=timedelta(minutes=15),
            refresh_token_ttl=timedelta(days=7),
            issuer="auth-service",
            audience="auth-api",
        )

    @pytest.fixture
    def account_id(self) -> UserId:
        return UserId(
            UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190c"),
        )

    @pytest.fixture
    def session_id(self) -> SessionId:
        return SessionId(
            UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d"),
        )

    async def test_issues_access_and_refresh_tokens(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        assert isinstance(tokens.access_token, str)
        assert isinstance(tokens.refresh_token, str)

        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.access_token != tokens.refresh_token

        assert tokens.token_type == "bearer"

    async def test_issues_access_token_with_expected_expiration(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
            clock: FakeClock,
    ) -> None:
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        assert tokens.access_token_expires_at == (
                clock.now() + timedelta(minutes=15)
        ).replace(microsecond=0)
        assert tokens.refresh_token_expires_at == (
                clock.now() + timedelta(days=7)
        ).replace(microsecond=0)

    async def test_verifies_issued_access_token(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        payload = token_service.verify_access_token(
            tokens.access_token,
        )

        assert payload.account_id == account_id
        assert payload.session_id == session_id
        assert payload.expires_at == tokens.access_token_expires_at

    async def test_rejects_unknown_or_malformed_access_token(
            self,
            token_service: JWTTokenService,
    ) -> None:
        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(
                "this-is-not-a-jwt",
            )

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    async def test_rejects_access_token_signed_with_other_secret(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
            clock: FakeClock,
    ) -> None:
        issuer_service = JWTTokenService(
            secret_key="first-secret-key-for-tests",
            clock=clock,
            issuer="auth-service",
            audience="auth-api",
        )
        verifier_service = JWTTokenService(
            secret_key="different-secret-key-for-tests",
            clock=clock,
            issuer="auth-service",
            audience="auth-api",
        )

        tokens = issuer_service.issue_tokens(account_id=account_id, session_id=session_id)

        with pytest.raises(AccessTokenInvalidError) as error:
            verifier_service.verify_access_token(
                tokens.access_token,
            )

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    async def test_rejects_expired_access_token(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
            clock: FakeClock,
    ) -> None:
        clock.advance(timedelta(minutes=-16))
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(
                tokens.access_token,
            )

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    async def test_rejects_refresh_token_as_access_token(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(
                tokens.refresh_token,
            )

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    async def test_creates_different_refresh_tokens_for_same_account(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        first_tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)
        second_tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        assert first_tokens.refresh_token != second_tokens.refresh_token

    async def test_hashes_refresh_token_deterministically(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        first_hash = token_service.hash_refresh_token(
            tokens.refresh_token,
        )
        second_hash = token_service.hash_refresh_token(
            tokens.refresh_token,
        )

        assert first_hash == second_hash
        assert first_hash != tokens.refresh_token

    async def test_creates_different_hashes_for_different_refresh_tokens(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        first_tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)
        second_tokens = token_service.issue_tokens(account_id=account_id, session_id=session_id)

        first_hash = token_service.hash_refresh_token(
            first_tokens.refresh_token,
        )
        second_hash = token_service.hash_refresh_token(
            second_tokens.refresh_token,
        )

        assert first_hash != second_hash

    def test_init_rejects_empty_secret_key(self, clock: FakeClock) -> None:
        with pytest.raises(ValueError, match="secret_key must not be empty"):
            JWTTokenService(secret_key="", clock=clock)

    def test_init_rejects_non_positive_access_token_ttl(self, clock: FakeClock) -> None:
        with pytest.raises(ValueError, match="access_token_ttl must be positive"):
            JWTTokenService(
                secret_key="valid-secret",
                clock=clock,
                access_token_ttl=timedelta(seconds=0),
            )

    def test_init_rejects_non_positive_refresh_token_ttl(self, clock: FakeClock) -> None:
        with pytest.raises(ValueError, match="refresh_token_ttl must be positive"):
            JWTTokenService(
                secret_key="valid-secret",
                clock=clock,
                refresh_token_ttl=timedelta(days=0),
            )

    def test_init_accepts_secret_str(
            self,
            clock: FakeClock,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        from pydantic import SecretStr

        service = JWTTokenService(
            secret_key=SecretStr("secret-from-secret-str"),
            clock=clock,
        )
        tokens = service.issue_tokens(account_id=account_id, session_id=session_id)
        payload = service.verify_access_token(tokens.access_token)

        assert payload.account_id == account_id

    def test_verify_rejects_wrong_issuer(
            self,
            clock: FakeClock,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        issuer = JWTTokenService(
            secret_key="shared-secret",
            clock=clock,
            issuer="issuer-a",
            audience="auth-api",
        )
        verifier = JWTTokenService(
            secret_key="shared-secret",
            clock=clock,
            issuer="issuer-b",
            audience="auth-api",
        )
        tokens = issuer.issue_tokens(account_id=account_id, session_id=session_id)

        with pytest.raises(AccessTokenInvalidError) as error:
            verifier.verify_access_token(tokens.access_token)

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    def test_verify_rejects_wrong_audience(
            self,
            clock: FakeClock,
            account_id: UserId,
            session_id: SessionId,
    ) -> None:
        issuer = JWTTokenService(
            secret_key="shared-secret",
            clock=clock,
            issuer="auth-service",
            audience="audience-a",
        )
        verifier = JWTTokenService(
            secret_key="shared-secret",
            clock=clock,
            issuer="auth-service",
            audience="audience-b",
        )
        tokens = issuer.issue_tokens(account_id=account_id, session_id=session_id)

        with pytest.raises(AccessTokenInvalidError) as error:
            verifier.verify_access_token(tokens.access_token)

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    def test_verify_rejects_non_access_typ(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            session_id: SessionId,
            clock: FakeClock,
    ) -> None:
        import jwt

        now = clock.now().replace(microsecond=0)
        token = jwt.encode(
            {
                "sub": str(account_id.value),
                "sid": str(session_id.value),
                "typ": "refresh",
                "iss": "auth-service",
                "aud": "auth-api",
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            key="test-secret-key-that-is-long-enough-for-tests",
            algorithm="HS256",
        )

        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(token)

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    def test_verify_rejects_missing_sid(
            self,
            token_service: JWTTokenService,
            account_id: UserId,
            clock: FakeClock,
    ) -> None:
        import jwt

        now = clock.now().replace(microsecond=0)
        token = jwt.encode(
            {
                "sub": str(account_id.value),
                "typ": "access",
                "iss": "auth-service",
                "aud": "auth-api",
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            key="test-secret-key-that-is-long-enough-for-tests",
            algorithm="HS256",
        )

        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(token)

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID

    def test_verify_rejects_invalid_sub_not_uuid(
            self,
            token_service: JWTTokenService,
            clock: FakeClock,
    ) -> None:
        import jwt

        now = clock.now().replace(microsecond=0)
        token = jwt.encode(
            {
                "sub": "not-a-uuid",
                "sid": str(UUID("018f4e9e-4ca1-7ca3-9e8f-6ab7d7c6190d")),
                "typ": "access",
                "iss": "auth-service",
                "aud": "auth-api",
                "iat": now,
                "exp": now + timedelta(minutes=15),
            },
            key="test-secret-key-that-is-long-enough-for-tests",
            algorithm="HS256",
        )

        with pytest.raises(AccessTokenInvalidError) as error:
            token_service.verify_access_token(token)

        assert error.value.code == ErrorCode.AUTH_ACCESS_TOKEN_INVALID
