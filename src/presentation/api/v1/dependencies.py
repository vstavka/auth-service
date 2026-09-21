from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.commands import (
    ChangeEmailHandler,
    ChangePasswordHandler,
    LoginAccountHandler,
    RefreshTokensHandler,
    RegisterAccountHandler,
    RevokeAllSessionsHandler,
    RevokeSessionHandler,
)
from src.application.dto import AccessTokenPayload
from src.application.ports.security import TokenService
from src.application.queries import GetMeHandler, ListSessionsHandler
from src.domain.exceptions.auth import AccessTokenInvalidError
from src.infrastructure.di.containers import Container

_http_bearer = HTTPBearer(auto_error=False)


def get_register_account_handler() -> RegisterAccountHandler:
    return Depends(Provide[Container.register_account_handler])


def get_login_account_handler() -> LoginAccountHandler:
    return Depends(Provide[Container.login_account_handler])


def get_refresh_tokens_handler() -> RefreshTokensHandler:
    return Depends(Provide[Container.refresh_tokens_handler])


def get_change_email_handler() -> ChangeEmailHandler:
    return Depends(Provide[Container.change_email_handler])


def get_change_password_handler() -> ChangePasswordHandler:
    return Depends(Provide[Container.change_password_handler])


def get_revoke_session_handler() -> RevokeSessionHandler:
    return Depends(Provide[Container.revoke_session_handler])


def get_revoke_all_sessions_handler() -> RevokeAllSessionsHandler:
    return Depends(Provide[Container.revoke_all_sessions_handler])


def get_get_me_handler() -> GetMeHandler:
    return Depends(Provide[Container.get_me_handler])


def get_list_sessions_handler() -> ListSessionsHandler:
    return Depends(Provide[Container.list_sessions_handler])


def get_token_service() -> TokenService:
    return Depends(Provide[Container.token_service])


@inject
async def get_access_context(
        credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
        token_service: TokenService = get_token_service(),
) -> AccessTokenPayload:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AccessTokenInvalidError()
    return token_service.verify_access_token(credentials.credentials)
