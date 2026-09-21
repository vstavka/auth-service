from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.application.dto import AccountPublic
from src.domain.enums import AccountStatus


class AccountPublicSchema(BaseModel):
    id: UUID
    email: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime


class ChangeEmailBody(BaseModel):
    email: EmailStr


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6, max_length=64)


def account_public_to_schema(account: AccountPublic) -> AccountPublicSchema:
    return AccountPublicSchema(
        id=account.id,
        email=account.email,
        status=account.status,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )
