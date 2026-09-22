from uuid import UUID

from dependency_injector.wiring import inject
from fastapi import APIRouter, Depends, status

from src.application.commands import RevokeAllSessionsHandler, RevokeSessionHandler
from src.application.dto import (
    AccessTokenPayload,
    ListSessionsQuery,
    RevokeAllSessionsRequest,
    RevokeSessionRequest,
)
from src.application.queries import ListSessionsHandler
from src.domain.value_objects import SessionId
from src.presentation.api.v1.dependencies import (
    get_access_context,
    get_list_sessions_handler,
    get_revoke_all_sessions_handler,
    get_revoke_session_handler,
)
from src.presentation.api.v1.schemas import SessionPublicSchema, session_public_to_schema

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionPublicSchema])
@inject
async def list_sessions(
        access: AccessTokenPayload = Depends(get_access_context),
        handler: ListSessionsHandler = get_list_sessions_handler(),
):
    sessions = await handler.execute(ListSessionsQuery(actor_id=access.account_id))
    return [session_public_to_schema(session) for session in sessions]


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def revoke_all_sessions(
        access: AccessTokenPayload = Depends(get_access_context),
        handler: RevokeAllSessionsHandler = get_revoke_all_sessions_handler(),
) -> None:
    await handler.execute(RevokeAllSessionsRequest(actor_id=access.account_id))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def revoke_session(
        session_id: UUID,
        access: AccessTokenPayload = Depends(get_access_context),
        handler: RevokeSessionHandler = get_revoke_session_handler(),
) -> None:
    await handler.execute(
        RevokeSessionRequest(
            actor_id=access.account_id,
            session_id=SessionId(session_id),
        ),
    )
