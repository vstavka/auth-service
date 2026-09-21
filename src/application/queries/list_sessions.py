from src.application.dto import ListSessionsQuery, SessionPublic, session_to_public
from src.application.ports.system import UnitOfWork
from src.application.services import require_active_account


class ListSessionsHandler:
    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: ListSessionsQuery) -> list[SessionPublic]:
        async with self._uow:
            account = await require_active_account(self._uow, query.actor_id)
            sessions = await self._uow.sessions.list_by_account_id(account.id)
        return [session_to_public(session) for session in sessions]
