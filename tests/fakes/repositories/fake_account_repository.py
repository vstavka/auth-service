from src.application.ports.repositories import AccountRepository
from src.domain.entities import Account
from src.domain.exceptions.email import EmailAlreadyRegisteredError
from src.domain.value_objects import Email, UserId


class FakeAccountRepository(AccountRepository):

    def __init__(self):
        self._accounts: dict[UserId, Account] = {}
        self._next_id = 1

    async def add(self, account: Account) -> None:
        if account.id is None:
            account.id = self._next_id
            self._next_id += 1
        self._accounts[account.public_id] = account

    async def get_by_id(self, account_id: UserId) -> Account | None:
        return self._accounts.get(account_id)

    async def get_by_email(self, email: Email) -> Account | None:
        for account in self._accounts.values():
            if account.email == email:
                return account
        return None

    async def get_by_internal_id(self, account_id: int) -> Account | None:
        for account in self._accounts.values():
            if account.id == account_id:
                return account
        return None

    async def save(self, account: Account) -> None:
        for existing in self._accounts.values():
            if existing.public_id != account.public_id and existing.email == account.email:
                raise EmailAlreadyRegisteredError(
                    details={"email": account.email.value},
                )
        self._accounts[account.public_id] = account
