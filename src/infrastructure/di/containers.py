from datetime import timedelta

from dependency_injector import containers, providers

from src.application.commands import (
    ChangeEmailHandler,
    ChangePasswordHandler,
    LoginAccountHandler,
    RefreshTokensHandler,
    RegisterAccountHandler,
    RevokeAllSessionsHandler,
    RevokeSessionHandler,
)
from src.application.queries import (
    GetAccountByIdHandler,
    GetAccountsByIdsHandler,
    GetMeHandler,
    ListSessionsHandler,
)
from src.application.services import OutboxRelay
from src.domain.services.password_policy import PasswordPolicy
from src.infrastructure.cache.factory import create_cache
from src.infrastructure.messaging.factory import create_event_publisher
from src.infrastructure.persistence.sqlalchemy.database import create_engine, create_session_maker
from src.infrastructure.persistence.sqlalchemy.sql_unit_of_work import SQLUnitOfWork
from src.infrastructure.security import Argon2PasswordHasher, JWTTokenService
from src.infrastructure.system import SystemClock, UUID7IdGenerator
from src.presentation.grpc.services import AccountGrpcService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    access_token_ttl = providers.Callable(
        timedelta, minutes=config.jwt.access_token_expire_minutes
    )
    refresh_token_ttl = providers.Callable(
        timedelta, days=config.jwt.refresh_token_expire_days
    )
    account_cache_ttl = providers.Callable(
        timedelta, seconds=config.cache.account_ttl_seconds
    )
    sessions_cache_ttl = providers.Callable(
        timedelta, seconds=config.cache.sessions_ttl_seconds
    )
    relay_poll_interval = providers.Callable(
        timedelta, seconds=config.events.relay_poll_interval_seconds
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

    cache = providers.Singleton(
        create_cache,
        backend=config.cache.backend,
        redis_url=config.redis.url,
    )
    event_publisher = providers.Singleton(
        create_event_publisher,
        events=config.events,
    )
    outbox_relay = providers.Factory(
        OutboxRelay,
        uow=unit_of_work,
        publisher=event_publisher,
        clock=clock,
        batch_size=config.events.relay_batch_size,
        poll_interval=relay_poll_interval,
    )

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
        cache=cache,
    )
    login_account_handler = providers.Factory(
        LoginAccountHandler,
        uow=unit_of_work,
        password_hasher=password_hasher,
        token_service=token_service,
        id_generator=id_generator,
        clock=clock,
        cache=cache,
    )
    refresh_tokens_handler = providers.Factory(
        RefreshTokensHandler,
        uow=unit_of_work,
        token_service=token_service,
        clock=clock,
        cache=cache,
    )
    change_email_handler = providers.Factory(
        ChangeEmailHandler,
        uow=unit_of_work,
        clock=clock,
        cache=cache,
    )
    change_password_handler = providers.Factory(
        ChangePasswordHandler,
        uow=unit_of_work,
        password_policy=password_policy,
        password_hasher=password_hasher,
        clock=clock,
        cache=cache,
    )
    revoke_session_handler = providers.Factory(
        RevokeSessionHandler,
        uow=unit_of_work,
        clock=clock,
        cache=cache,
    )
    revoke_all_sessions_handler = providers.Factory(
        RevokeAllSessionsHandler,
        uow=unit_of_work,
        clock=clock,
        cache=cache,
    )
    get_me_handler = providers.Factory(
        GetMeHandler,
        uow=unit_of_work,
        cache=cache,
        ttl=account_cache_ttl,
    )
    get_account_by_id_handler = providers.Factory(
        GetAccountByIdHandler,
        uow=unit_of_work,
        cache=cache,
        ttl=account_cache_ttl,
    )
    get_accounts_by_ids_handler = providers.Factory(
        GetAccountsByIdsHandler,
        uow=unit_of_work,
        cache=cache,
        ttl=account_cache_ttl,
    )
    list_sessions_handler = providers.Factory(
        ListSessionsHandler,
        uow=unit_of_work,
        cache=cache,
        ttl=sessions_cache_ttl,
    )
    account_grpc_service = providers.Factory(
        AccountGrpcService,
        get_account_by_id=get_account_by_id_handler,
        get_accounts_by_ids=get_accounts_by_ids_handler,
    )
