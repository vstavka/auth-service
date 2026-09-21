from pydantic import BaseModel, EmailStr, Field

from src.application.dto import RegisterRequest


class RegisterAccountRequest(BaseModel):
    """Request schema for account registration."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=64)


def register_request_to_application(payload: RegisterAccountRequest) -> "RegisterRequest":
    return RegisterRequest(
        email=str(payload.email),
        password=payload.password,
    )
