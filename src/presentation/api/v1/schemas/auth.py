from pydantic import BaseModel, EmailStr, Field

from src.application.dto import (
    LoginRequest,
    RefreshTokensRequest,
    RegisterRequest,
)


class RegisterAccountRequest(BaseModel):
    """Request schema for account registration."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=64)


class LoginAccountRequest(BaseModel):
    """Request schema for account login."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=64)


class RefreshTokensBody(BaseModel):
    refresh_token: str = Field(min_length=1)


def register_request_to_application(
        payload: RegisterAccountRequest,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
) -> RegisterRequest:
    return RegisterRequest(
        email=str(payload.email),
        password=payload.password,
        ip=ip,
        user_agent=user_agent,
    )


def login_request_to_application(
        payload: LoginAccountRequest,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
) -> LoginRequest:
    return LoginRequest(
        email=str(payload.email),
        password=payload.password,
        ip=ip,
        user_agent=user_agent,
    )


def refresh_tokens_to_application(payload: RefreshTokensBody) -> RefreshTokensRequest:
    return RefreshTokensRequest(refresh_token=payload.refresh_token)
