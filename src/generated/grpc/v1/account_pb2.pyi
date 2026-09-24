from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AccountStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ACCOUNT_STATUS_UNSPECIFIED: _ClassVar[AccountStatus]
    ACCOUNT_STATUS_ACTIVE: _ClassVar[AccountStatus]
    ACCOUNT_STATUS_DISABLED: _ClassVar[AccountStatus]
    ACCOUNT_STATUS_DELETED: _ClassVar[AccountStatus]
ACCOUNT_STATUS_UNSPECIFIED: AccountStatus
ACCOUNT_STATUS_ACTIVE: AccountStatus
ACCOUNT_STATUS_DISABLED: AccountStatus
ACCOUNT_STATUS_DELETED: AccountStatus

class Account(_message.Message):
    __slots__ = ("id", "email", "status")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    status: AccountStatus
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., status: _Optional[_Union[AccountStatus, str]] = ...) -> None: ...

class GetAccountByIdRequest(_message.Message):
    __slots__ = ("account_id",)
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    account_id: str
    def __init__(self, account_id: _Optional[str] = ...) -> None: ...

class GetAccountByIdResponse(_message.Message):
    __slots__ = ("account",)
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    account: Account
    def __init__(self, account: _Optional[_Union[Account, _Mapping]] = ...) -> None: ...

class GetAccountsByIdsRequest(_message.Message):
    __slots__ = ("account_ids",)
    ACCOUNT_IDS_FIELD_NUMBER: _ClassVar[int]
    account_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, account_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetAccountsByIdsResponse(_message.Message):
    __slots__ = ("accounts",)
    ACCOUNTS_FIELD_NUMBER: _ClassVar[int]
    accounts: _containers.RepeatedCompositeFieldContainer[Account]
    def __init__(self, accounts: _Optional[_Iterable[_Union[Account, _Mapping]]] = ...) -> None: ...
