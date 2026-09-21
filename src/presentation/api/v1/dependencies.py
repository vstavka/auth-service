from dependency_injector.wiring import Provide
from src.infrastructure.di.containers import Container
from fastapi import Depends

from src.application.commands import RegisterAccountHandler


def get_register_account_handler() -> RegisterAccountHandler:
    return Depends(Provide[Container.register_account_handler])