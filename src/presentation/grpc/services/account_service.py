from uuid import UUID

from grpc import StatusCode, aio

from src.application.dto import GetAccountByIdQuery, GetAccountsByIdsQuery
from src.application.dto.account_public import AccountPublic
from src.application.queries import GetAccountByIdHandler, GetAccountsByIdsHandler
from src.domain.enums import AccountStatus
from src.domain.exceptions.auth import UserNotFoundError
from src.domain.value_objects import UserId
from src.generated.grpc.v1 import account_pb2, account_pb2_grpc


class AccountGrpcService(account_pb2_grpc.AccountServiceServicer):
    def __init__(
        self,
        get_account_by_id: GetAccountByIdHandler,
        get_accounts_by_ids: GetAccountsByIdsHandler,
    ) -> None:
        self._get_account_by_id = get_account_by_id
        self._get_accounts_by_ids = get_accounts_by_ids

    async def GetAccountById(
        self,
        request: account_pb2.GetAccountByIdRequest,
        context: aio.ServicerContext,
    ) -> account_pb2.GetAccountByIdResponse:
        try:
            account_id = UserId(UUID(request.account_id))
        except (ValueError, TypeError):
            await context.abort(
                StatusCode.INVALID_ARGUMENT,
                "account_id must be a valid UUID",
            )

        try:
            result = await self._get_account_by_id.execute(
                GetAccountByIdQuery(account_id=account_id)
            )
        except UserNotFoundError:
            await context.abort(StatusCode.NOT_FOUND, "Account not found")

        return account_pb2.GetAccountByIdResponse(account=self._to_account(result))

    async def GetAccountsByIds(
        self,
        request: account_pb2.GetAccountsByIdsRequest,
        context: aio.ServicerContext,
    ) -> account_pb2.GetAccountsByIdsResponse:
        account_ids: list[UserId] = []
        for raw_id in request.account_ids:
            try:
                account_ids.append(UserId(UUID(raw_id)))
            except (ValueError, TypeError):
                await context.abort(
                    StatusCode.INVALID_ARGUMENT,
                    f"account_id must be a valid UUID: {raw_id}",
                )

        results = await self._get_accounts_by_ids.execute(
            GetAccountsByIdsQuery(account_ids=account_ids)
        )
        return account_pb2.GetAccountsByIdsResponse(
            accounts=[self._to_account(item) for item in results]
        )

    def _to_account(self, account: AccountPublic) -> account_pb2.Account:
        return account_pb2.Account(
            id=str(account.id),
            email=account.email,
            status=self._to_proto_status(account.status),
        )

    @staticmethod
    def _to_proto_status(status: AccountStatus) -> int:
        return {
            AccountStatus.ACTIVE: account_pb2.ACCOUNT_STATUS_ACTIVE,
            AccountStatus.DISABLED: account_pb2.ACCOUNT_STATUS_DISABLED,
            AccountStatus.DELETED: account_pb2.ACCOUNT_STATUS_DELETED,
        }[status]
