from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import AppError
from src.shared.errors.codes import ErrorCode

_ERROR_STATUS: dict[ErrorCode, int] = {
    ErrorCode.AUTH_INVALID_EMAIL: 422,
    ErrorCode.AUTH_INVALID_PASSWORD: 422,
    ErrorCode.AUTH_EMAIL_ALREADY_REGISTERED: 409,
    ErrorCode.AUTH_INVALID_CREDENTIALS: 401,
    ErrorCode.AUTH_ACCESS_TOKEN_INVALID: 401,
    ErrorCode.AUTH_REFRESH_TOKEN_INVALID: 401,
    ErrorCode.AUTH_EMAIL_NOT_VERIFIED: 403,
    ErrorCode.AUTH_ACCOUNT_DISABLED: 403,
    ErrorCode.USER_NOT_FOUND: 404,
    ErrorCode.INTERNAL_ERROR: 500,
}


def _app_error_body(exc: AppError) -> dict:
    return {
        "code": exc.code.value,
        "message": exc.message,
        "details": exc.details,
    }


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    status_code = _ERROR_STATUS.get(exc.code, 400)
    return JSONResponse(status_code=status_code, content=_app_error_body(exc))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
