from dependency_injector.wiring import inject
from fastapi import APIRouter, Depends, status

from src.application.commands import ChangeEmailHandler, ChangePasswordHandler
from src.application.dto import (
    AccessTokenPayload,
    ChangeEmailRequest,
    ChangePasswordRequest,
    GetMeQuery,
)
from src.application.queries import GetMeHandler
from src.presentation.api.v1.dependencies import (
    get_access_context,
    get_change_email_handler,
    get_change_password_handler,
    get_get_me_handler,
)
from src.presentation.api.v1.schemas import (
    AccountPublicSchema,
    ChangeEmailBody,
    ChangePasswordBody,
    account_public_to_schema,
)

router = APIRouter(tags=["me"])


@router.get("/me", response_model=AccountPublicSchema)
@inject
async def get_me(
        access: AccessTokenPayload = Depends(get_access_context),
        handler: GetMeHandler = get_get_me_handler(),
):
    account = await handler.execute(GetMeQuery(actor_id=access.account_id))
    return account_public_to_schema(account)


@router.patch("/me/email", response_model=AccountPublicSchema)
@inject
async def change_email(
        payload: ChangeEmailBody,
        access: AccessTokenPayload = Depends(get_access_context),
        handler: ChangeEmailHandler = get_change_email_handler(),
):
    account = await handler.execute(
        ChangeEmailRequest(
            actor_id=access.account_id,
            email=str(payload.email),
        ),
    )
    return account_public_to_schema(account)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def change_password(
        payload: ChangePasswordBody,
        access: AccessTokenPayload = Depends(get_access_context),
        handler: ChangePasswordHandler = get_change_password_handler(),
) -> None:
    await handler.execute(
        ChangePasswordRequest(
            actor_id=access.account_id,
            current_password=payload.current_password,
            new_password=payload.new_password,
            current_session_id=access.session_id,
        ),
    )
