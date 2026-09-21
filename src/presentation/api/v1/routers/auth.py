# src/presentation/api/v1/routers/auth.py
from fastapi import APIRouter, Depends, Request, status
from dependency_injector.wiring import inject

from src.application.commands import (
    LoginAccountHandler,
    RefreshTokensHandler,
    RegisterAccountHandler,
    RevokeSessionHandler,
)
from src.application.dto import AccessTokenPayload, RevokeSessionRequest
from src.presentation.api.v1.dependencies import (
    get_access_context,
    get_login_account_handler,
    get_refresh_tokens_handler,
    get_register_account_handler,
    get_revoke_session_handler,
)
from src.presentation.api.v1.request_meta import request_ip, request_user_agent
from src.presentation.api.v1.schemas import (
    LoginAccountRequest,
    RefreshTokensBody,
    RegisterAccountRequest,
    TokenPairSchema,
    login_request_to_application,
    refresh_tokens_to_application,
    register_request_to_application,
    token_pair_to_schema,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenPairSchema,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def register(
        payload: RegisterAccountRequest,
        request: Request,
        handler: RegisterAccountHandler = get_register_account_handler(),
):
    token_pair = await handler.execute(
        register_request_to_application(
            payload,
            ip=request_ip(request),
            user_agent=request_user_agent(request),
        ),
    )
    return token_pair_to_schema(token_pair)


@router.post("/login", response_model=TokenPairSchema)
@inject
async def login(
        payload: LoginAccountRequest,
        request: Request,
        handler: LoginAccountHandler = get_login_account_handler(),
):
    token_pair = await handler.execute(
        login_request_to_application(
            payload,
            ip=request_ip(request),
            user_agent=request_user_agent(request),
        ),
    )
    return token_pair_to_schema(token_pair)


@router.post("/refresh", response_model=TokenPairSchema)
@inject
async def refresh(
        payload: RefreshTokensBody,
        handler: RefreshTokensHandler = get_refresh_tokens_handler(),
):
    token_pair = await handler.execute(refresh_tokens_to_application(payload))
    return token_pair_to_schema(token_pair)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(
        access: AccessTokenPayload = Depends(get_access_context),
        handler: RevokeSessionHandler = get_revoke_session_handler(),
) -> None:
    await handler.execute(
        RevokeSessionRequest(
            actor_id=access.account_id,
            session_id=access.session_id,
        ),
    )
