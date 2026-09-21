# src/presentation/api/v1/routers/auth.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject

from src.application.commands import RegisterAccountHandler
from src.presentation.api.v1.dependencies import  get_register_account_handler
from src.presentation.api.v1.schemas import RegisterAccountRequest, register_request_to_application
from src.presentation.api.v1.schemas.token import TokenPairSchema, token_pair_to_schema


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPairSchema)
@inject
async def register(
    payload: RegisterAccountRequest,
    handler: RegisterAccountHandler = get_register_account_handler(),
):
    token_pair = await handler.execute(register_request_to_application(payload))
    return token_pair_to_schema(token_pair)