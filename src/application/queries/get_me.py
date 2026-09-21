from src.application.dto import AccountPublic, GetMeQuery, account_to_public
from src.application.ports.system import UnitOfWork
from src.application.services import require_active_account


class GetMeHandler:
    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: GetMeQuery) -> AccountPublic:
        async with self._uow:
            account = await require_active_account(self._uow, query.actor_id)
        return account_to_public(account)
