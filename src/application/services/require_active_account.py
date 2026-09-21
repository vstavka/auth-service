from src.application.ports.system import UnitOfWork
from src.domain.entities import Account
from src.domain.exceptions.auth import AccountDisabledError, UserNotFoundError
from src.domain.value_objects import UserId


async def require_active_account(
        uow: UnitOfWork,
        actor_id: UserId,
) -> Account:
    account = await uow.accounts.get_by_id(actor_id)
    if account is None:
        raise UserNotFoundError()
    if not account.is_active:
        raise AccountDisabledError()
    if account.id is None:
        raise RuntimeError("Account id must be assigned after persist")
    return account
