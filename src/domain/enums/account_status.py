from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"
