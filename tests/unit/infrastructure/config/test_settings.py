import pytest
from pydantic import SecretStr, ValidationError

from src.infrastructure.config.settings import (
    AppSettings,
    CacheSettings,
    DatabaseSettings,
    EventsSettings,
    JWTSettings,
    LoggingSettings,
    RedisSettings,
    Settings,
)


@pytest.mark.unit
class TestDatabaseSettings:
    def test_database_settings_url_postgres(self) -> None:
        settings = DatabaseSettings(
            type="postgres",
            host="db.example.com",
            port=5433,
            name="auth",
            username="user",
            password=SecretStr("s3cret"),
            _env_file=None,
        )

        assert settings.url == (
            "postgresql+asyncpg://user:s3cret@db.example.com:5433/auth"
        )

    def test_database_settings_url_sqlite(self) -> None:
        settings = DatabaseSettings(type="sqlite", name="local_auth", _env_file=None)

        assert settings.url == "sqlite+aiosqlite:///local_auth.db"


@pytest.mark.unit
class TestJWTSettings:
    def test_jwt_settings_requires_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

        with pytest.raises(ValidationError):
            JWTSettings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.unit
class TestSettings:
    def test_settings_load_from_env_prefixes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_NAME", "custom-auth")
        monkeypatch.setenv("APP_ENVIRONMENT", "staging")
        monkeypatch.setenv("DB_TYPE", "sqlite")
        monkeypatch.setenv("DB_NAME", "env_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "env-secret-key")
        monkeypatch.setenv("JWT_ALGORITHM", "HS384")
        monkeypatch.setenv("LOGGING_LEVEL", "DEBUG")

        settings = Settings(
            app=AppSettings(_env_file=None),
            db=DatabaseSettings(_env_file=None),
            jwt=JWTSettings(_env_file=None),
            logging=LoggingSettings(_env_file=None),
            _env_file=None,
        )

        assert settings.app.name == "custom-auth"
        assert settings.app.environment == "staging"
        assert settings.db.type == "sqlite"
        assert settings.db.name == "env_db"
        assert settings.jwt.secret_key.get_secret_value() == "env-secret-key"
        assert settings.jwt.algorithm == "HS384"
        assert settings.logging.level == "DEBUG"

    def test_settings_nested_defaults(self) -> None:
        settings = Settings(
            app=AppSettings(_env_file=None),
            db=DatabaseSettings(_env_file=None),
            jwt=JWTSettings(secret_key="required-secret", _env_file=None),
            logging=LoggingSettings(_env_file=None),
            cache=CacheSettings(_env_file=None),
            events=EventsSettings(_env_file=None),
            _env_file=None,
        )

        assert settings.app.name == "auth-service"
        assert settings.app.version == "0.1.0"
        assert settings.db.type == "postgres"
        assert settings.logging.level == "INFO"
        assert settings.jwt.secret_key.get_secret_value() == "required-secret"
        assert settings.cache.backend == "memory"
        assert settings.events.publisher == "memory"


@pytest.mark.unit
class TestCacheAndEventsSettings:
    def test_cache_and_events_load_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CACHE_BACKEND", "redis")
        monkeypatch.setenv("CACHE_ACCOUNT_TTL_SECONDS", "30")
        monkeypatch.setenv("CACHE_SESSIONS_TTL_SECONDS", "45")
        monkeypatch.setenv("REDIS_HOST", "redis.internal")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_DB", "2")
        monkeypatch.setenv("REDIS_PASSWORD", "secret")
        monkeypatch.setenv("EVENTS_PUBLISHER", "kafka")
        monkeypatch.setenv("EVENTS_FILE_PATH", "/tmp/events.jsonl")
        monkeypatch.setenv("EVENTS_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        monkeypatch.setenv("EVENTS_KAFKA_CLIENT_ID", "auth-outbox")
        monkeypatch.setenv("EVENTS_RELAY_POLL_INTERVAL_SECONDS", "3.5")
        monkeypatch.setenv("EVENTS_RELAY_BATCH_SIZE", "10")

        cache = CacheSettings(_env_file=None)
        redis = RedisSettings(_env_file=None)
        events = EventsSettings(_env_file=None)

        assert cache.backend == "redis"
        assert cache.account_ttl_seconds == 30
        assert cache.sessions_ttl_seconds == 45
        assert redis.url == "redis://:secret@redis.internal:6380/2"
        assert events.publisher == "kafka"
        assert events.file_path == "/tmp/events.jsonl"
        assert events.kafka_bootstrap_servers == "kafka:9092"
        assert events.kafka_client_id == "auth-outbox"
        assert events.relay_poll_interval_seconds == 3.5
        assert events.relay_batch_size == 10

    def test_redis_url_without_password(self) -> None:
        redis = RedisSettings(_env_file=None)
        assert redis.url == "redis://localhost:6379/0"
