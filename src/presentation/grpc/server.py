import logging

from grpc import aio

from src.generated.grpc.v1 import account_pb2_grpc
from src.presentation.grpc.interceptors import LoggingInterceptor
from src.presentation.grpc.services import AccountGrpcService

logger = logging.getLogger(__name__)


async def start_grpc_server(
    *,
    account_service: AccountGrpcService,
    host: str,
    port: int,
    slow_request_threshold_seconds: float = 3.0,
) -> aio.Server:
    server = aio.server(
        interceptors=[
            LoggingInterceptor(
                slow_request_threshold_seconds=slow_request_threshold_seconds,
            ),
        ],
    )
    account_pb2_grpc.add_AccountServiceServicer_to_server(account_service, server)
    listen_addr = f"{host}:{port}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info("gRPC server started", extra={"listen_addr": listen_addr})
    return server
