from src.application.dto import TokenPair
from src.application.ports.security import TokenService
from src.application.ports.system import Clock, IdGenerator, UnitOfWork
from src.domain.entities import Account, Session
from src.domain.value_objects import RefreshTokenHash, SessionId


async def issue_session(
        *,
        uow: UnitOfWork,
        token_service: TokenService,
        id_generator: IdGenerator,
        clock: Clock,
        account: Account,
        ip: str | None = None,
        user_agent: str | None = None,
        device_info: str | None = None,
) -> TokenPair:
    if account.id is None:
        raise RuntimeError("Account id must be assigned after persist")

    session_id = SessionId(id_generator.new())
    tokens = token_service.issue_tokens(
        account_id=account.public_id,
        session_id=session_id,
    )
    session = Session.create(
        public_id=session_id,
        account_id=account.id,
        refresh_token_hash=RefreshTokenHash(
            token_service.hash_refresh_token(tokens.refresh_token),
        ),
        now=clock.now(),
        expires_at=tokens.refresh_token_expires_at,
        ip=ip,
        user_agent=user_agent,
        device_info=device_info,
    )
    await uow.sessions.add(session)
    return tokens
