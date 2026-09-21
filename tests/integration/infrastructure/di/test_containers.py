from datetime import timedelta

import pytest

from src.application.commands import RegisterAccountHandler
from src.infrastructure.di.containers import Container
from src.infrastructure.security import Argon2PasswordHasher, JWTTokenService
from src.infrastructure.system import SystemClock, UUID7IdGenerator
from src.infrastructure.persistence.sqlalchemy.sql_unit_of_work import SQLUnitOfWork


@pytest.mark.integration
class TestContainer:
    @pytest.fixture
    def container(self) -> Container:
        container = Container()
        container.config.from_dict(
            {
                "app": {
                    "name": "auth-service-test",
                    "version": "0.1.0",
                    "environment": "development",
                },
                "db": {
                    "url": "sqlite+aiosqlite:///:memory:",
                },
                "jwt": {
                    "secret_key": "container-test-secret-key",
                    "algorithm": "HS256",
                    "access_token_expire_minutes": 20,
                    "refresh_token_expire_days": 14,
                },
            }
        )
        return container

    def test_providers_resolve_after_config_from_dict(self, container: Container) -> None:
        assert isinstance(container.clock(), SystemClock)
        assert isinstance(container.id_generator(), UUID7IdGenerator)
        assert isinstance(container.password_hasher(), Argon2PasswordHasher)
        assert isinstance(container.token_service(), JWTTokenService)
        assert isinstance(container.unit_of_work(), SQLUnitOfWork)
        assert isinstance(container.register_account_handler(), RegisterAccountHandler)

    def test_token_service_receives_jwt_ttl_issuer_algorithm(
            self,
            container: Container,
    ) -> None:
        token_service = container.token_service()

        assert token_service._access_token_ttl == timedelta(minutes=20)
        assert token_service._refresh_token_ttl == timedelta(days=14)
        assert token_service._issuer == "auth-service-test"
        assert token_service._algorithm == "HS256"
