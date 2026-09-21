from datetime import timedelta

from dependency_injector import containers, providers

from src.application.commands import RegisterAccountHandler
from src.domain.services.password_policy import PasswordPolicy
from src.infrastructure.persistence.sqlalchemy.database import create_engine, create_session_maker
from src.infrastructure.persistence.sqlalchemy.sql_unit_of_work import SQLUnitOfWork
from src.infrastructure.security import Argon2PasswordHasher, JWTTokenService
from src.infrastructure.system import SystemClock, UUID7IdGenerator


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    access_token_ttl = providers.Callable(
        timedelta, minutes=config.jwt.access_token_expire_minutes
    )
    refresh_token_ttl = providers.Callable(
        timedelta, days=config.jwt.refresh_token_expire_days
    )
    clock = providers.Singleton(SystemClock)
    id_generator = providers.Singleton(UUID7IdGenerator)
    password_hasher = providers.Singleton(Argon2PasswordHasher)
    password_policy = providers.Singleton(PasswordPolicy)


    engine = providers.Singleton(
        create_engine,
        url=config.db.url,
    )
    session_factory = providers.Singleton(create_session_maker, engine=engine)
    unit_of_work = providers.Factory(SQLUnitOfWork, session_factory=session_factory)



    token_service = providers.Singleton(
        JWTTokenService,
        secret_key=config.jwt.secret_key,
        clock=clock,
        access_token_ttl=access_token_ttl,
        refresh_token_ttl=refresh_token_ttl,
        issuer=config.app.name,
        audience="auth-api",
        algorithm=config.jwt.algorithm,
    )





    register_account_handler = providers.Factory(
        RegisterAccountHandler,
        uow=unit_of_work,
        clock=clock,
        id_generator=id_generator,
        password_hasher=password_hasher,
        token_service=token_service,
        password_policy=password_policy,
    )
