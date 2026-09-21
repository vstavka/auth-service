# src/infrastructure/config/settings.py
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    name: str = "auth-service"
    version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DB_", env_file=".env", extra="ignore")

    type: Literal["postgres", "sqlite"] = "postgres"
    host: str = "localhost"
    port: int = 5432
    name: str = "auth_db"
    username: str = "postgres"
    password: SecretStr = SecretStr("postgres")


    @computed_field
    @property
    def url(self) -> str:
        if self.type == "postgres":
            return (
                f"postgresql+asyncpg://{self.username}:"
                f"{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"
            )
        return f"sqlite+aiosqlite:///{self.name}.db"


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_", env_file=".env", extra="ignore")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGGING_", env_file=".env", extra="ignore")

    level: str = "INFO"
    path: str | None = None
    slow_request_threshold_seconds: float = 3.0


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="ignore")

    app: AppSettings = Field(default_factory=AppSettings)
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)