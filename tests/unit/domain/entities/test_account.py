from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.domain.entities import Account
from src.domain.enums import AccountStatus
from src.domain.value_objects import Email, PasswordHash, UserId

ACCOUNT_ID = 1
ACCOUNT_PUBLIC_ID = UserId(
    value=UUID("12345678-1234-5678-1234-567812345678")
)
EMAIL = Email("User@yandex.ru")
INITIAL_PASSWORD_HASH = PasswordHash(
    "e99a18exampleExampleExampleExampleExampleExampleExample"
)
CREATED_AT = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def account() -> Account:
    return Account.create(
        id=ACCOUNT_ID,
        public_id=ACCOUNT_PUBLIC_ID,
        email=EMAIL,
        password_hash=INITIAL_PASSWORD_HASH,
        now=CREATED_AT,
    )


@pytest.mark.unit
class TestAccount:
    def test_create_account(self, account: Account):
        assert account.id == ACCOUNT_ID
        assert account.public_id == ACCOUNT_PUBLIC_ID
        assert account.email == EMAIL
        assert account.password_hash == INITIAL_PASSWORD_HASH
        assert account.status is AccountStatus.ACTIVE
        assert account.created_at == CREATED_AT
        assert account.updated_at == CREATED_AT
        assert account.is_active is True
        events = account.events
        assert len(events) == 1
        event = events[0]
        assert event.account_id == ACCOUNT_PUBLIC_ID
        assert event.email == EMAIL
        assert event.occurred_at == CREATED_AT

        pulled = account.pull_events()
        assert pulled == list(events)
        assert account.events == ()
        assert account.pull_events() == []

    def test_change_password(self, account: Account):
        changed_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )
        new_password_hash = PasswordHash(
            "e99a20exampleExampleExampleExampleExampleExampleExample"
        )

        account.change_password(
            new_password_hash=new_password_hash,
            now=changed_at,
        )

        assert account.password_hash == new_password_hash
        assert account.created_at == CREATED_AT
        assert account.updated_at == changed_at
        assert account.status is AccountStatus.ACTIVE
        assert account.is_active is True

    def test_change_email(self, account: Account):
        changed_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )
        new_email = Email("new.user@yandex.ru")

        account.change_email(email=new_email, now=changed_at)

        assert account.email == new_email
        assert account.created_at == CREATED_AT
        assert account.updated_at == changed_at

    def test_change_email_same_value_does_not_change_updated_at(self, account: Account):
        attempted_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )

        account.change_email(email=EMAIL, now=attempted_at)

        assert account.email == EMAIL
        assert account.updated_at == CREATED_AT

    def test_disable_account(self, account: Account):
        disabled_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )

        account.disable(disabled_at)

        assert account.status is AccountStatus.DISABLED
        assert account.created_at == CREATED_AT
        assert account.updated_at == disabled_at
        assert account.is_active is False

    def test_disabling_account_twice_does_not_change_updated_at(
            self,
            account: Account,
    ):
        first_disabled_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )
        second_disabled_at = datetime(
            2026,
            9,
            15,
            18,
            10,
            tzinfo=timezone.utc,
        )

        account.disable(first_disabled_at)
        account.disable(second_disabled_at)

        assert account.status is AccountStatus.DISABLED
        assert account.updated_at == first_disabled_at
        assert account.is_active is False

    def test_enable_disabled_account(self, account: Account):
        disabled_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )
        enabled_at = datetime(
            2026,
            9,
            15,
            18,
            10,
            tzinfo=timezone.utc,
        )
        account.disable(disabled_at)

        account.enable(enabled_at)

        assert account.status is AccountStatus.ACTIVE
        assert account.created_at == CREATED_AT
        assert account.updated_at == enabled_at
        assert account.is_active is True

    def test_enabling_active_account_does_not_change_updated_at(
            self,
            account: Account,
    ):
        attempted_enable_at = datetime(
            2026,
            9,
            15,
            18,
            5,
            tzinfo=timezone.utc,
        )

        account.enable(attempted_enable_at)

        assert account.status is AccountStatus.ACTIVE
        assert account.updated_at == CREATED_AT
        assert account.is_active is True

    def test_create_without_id_sets_id_to_none(self):
        account = Account.create(
            public_id=ACCOUNT_PUBLIC_ID,
            email=EMAIL,
            password_hash=INITIAL_PASSWORD_HASH,
            now=CREATED_AT,
        )

        assert account.id is None

    def test_disable_from_deleted_sets_disabled_and_updates_updated_at(self):
        deleted_at = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
        disabled_at = datetime(2026, 9, 15, 18, 5, tzinfo=timezone.utc)
        account = Account(
            id=ACCOUNT_ID,
            public_id=ACCOUNT_PUBLIC_ID,
            email=EMAIL,
            password_hash=INITIAL_PASSWORD_HASH,
            status=AccountStatus.DELETED,
            created_at=deleted_at,
            updated_at=deleted_at,
        )

        account.disable(disabled_at)

        assert account.status is AccountStatus.DISABLED
        assert account.updated_at == disabled_at

    def test_enable_from_deleted_is_noop(self):
        deleted_at = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
        attempted_at = datetime(2026, 9, 15, 18, 5, tzinfo=timezone.utc)
        account = Account(
            id=ACCOUNT_ID,
            public_id=ACCOUNT_PUBLIC_ID,
            email=EMAIL,
            password_hash=INITIAL_PASSWORD_HASH,
            status=AccountStatus.DELETED,
            created_at=deleted_at,
            updated_at=deleted_at,
        )

        account.enable(attempted_at)

        assert account.status is AccountStatus.DELETED
        assert account.updated_at == deleted_at

    def test_is_active_false_when_deleted(self):
        now = datetime(2026, 9, 15, 18, 0, tzinfo=timezone.utc)
        account = Account(
            id=ACCOUNT_ID,
            public_id=ACCOUNT_PUBLIC_ID,
            email=EMAIL,
            password_hash=INITIAL_PASSWORD_HASH,
            status=AccountStatus.DELETED,
            created_at=now,
            updated_at=now,
        )

        assert account.is_active is False
