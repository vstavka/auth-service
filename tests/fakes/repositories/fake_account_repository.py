from src.application.ports.repositories import AccountRepository
from src.domain.entities import Account
from src.domain.value_objects import Email, UserId


class FakeAccountRepository(AccountRepository):

    def __init__(self):
        self._accounts: dict[UserId, Account] = {}

    async def add(self, account: Account) -> None:
        self._accounts[account.id] = account

    async def get_by_id(self, account_id: UserId) -> Account | None:
        return self._accounts.get(account_id)

    async def get_by_email(self, email: Email) -> Account | None:
        for account in self._accounts.values():
            if account.email == email:
                return account
        return None
