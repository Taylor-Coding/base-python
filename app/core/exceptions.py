import logging
from enum import Enum

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.common.response import ApiError
from app.integrations.http_client import ExternalApiError

logger = logging.getLogger(__name__)

VALIDATION_ERROR = "VALIDATION_ERROR"
SERVER_ERROR = "SERVER_ERROR"


# --------------------------------------------------------------------------- #
# App Exception Code                                                           #
# --------------------------------------------------------------------------- #


class AppExceptionCode(str, Enum):
    # Auth
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    MISSING_TOKEN = "MISSING_TOKEN"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"

    FORBIDDEN_ROLE = "FORBIDDEN_ROLE"

    # User
    NOT_FOUND_USER = "NOT_FOUND_USER"
    DUPLICATE_EMAIL = "DUPLICATE_EMAIL"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INACTIVE_USER = "INACTIVE_USER"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"


    @property
    def http_status(self) -> int:
        return _STATUS_MAP[self]

    @property
    def message(self) -> str:
        return _MESSAGE_MAP[self]


_STATUS_MAP: dict[AppExceptionCode, int] = {
    AppExceptionCode.INVALID_TOKEN: status.HTTP_401_UNAUTHORIZED,
    AppExceptionCode.EXPIRED_TOKEN: status.HTTP_401_UNAUTHORIZED,
    AppExceptionCode.MISSING_TOKEN: status.HTTP_401_UNAUTHORIZED,
    AppExceptionCode.UNAUTHORIZED_ACCESS: status.HTTP_401_UNAUTHORIZED,
    AppExceptionCode.FORBIDDEN_ROLE: status.HTTP_403_FORBIDDEN,
    AppExceptionCode.NOT_FOUND_USER: status.HTTP_404_NOT_FOUND,
    AppExceptionCode.DUPLICATE_EMAIL: status.HTTP_409_CONFLICT,
    AppExceptionCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    AppExceptionCode.INACTIVE_USER: status.HTTP_403_FORBIDDEN,
    AppExceptionCode.ACCOUNT_LOCKED: status.HTTP_403_FORBIDDEN,
}

_MESSAGE_MAP: dict[AppExceptionCode, str] = {
    AppExceptionCode.INVALID_TOKEN: "잘못된 토큰입니다.",
    AppExceptionCode.EXPIRED_TOKEN: "만료된 토큰입니다.",
    AppExceptionCode.MISSING_TOKEN: "토큰이 누락되었습니다.",
    AppExceptionCode.UNAUTHORIZED_ACCESS: "인증되지 않은 접근입니다.",
    AppExceptionCode.FORBIDDEN_ROLE: "접근 권한이 없습니다.",
    AppExceptionCode.NOT_FOUND_USER: "사용자를 찾을 수 없습니다.",
    AppExceptionCode.DUPLICATE_EMAIL: "이미 사용 중인 이메일입니다.",
    AppExceptionCode.INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
    AppExceptionCode.INACTIVE_USER: "비활성화된 계정입니다.",
    AppExceptionCode.ACCOUNT_LOCKED: "계정이 잠겼습니다. 잠시 후 다시 시도해주세요.",
}


# --------------------------------------------------------------------------- #
# App Exception                                                                #
# --------------------------------------------------------------------------- #


class AppException(Exception):
    def __init__(self, code: AppExceptionCode, message: str | None = None) -> None:
        _message = message or code.message
        super().__init__(_message)
        self.code = code
        self.http_status = code.http_status
        self.message = _message


# --------------------------------------------------------------------------- #
# Global Exception Handlers                                                    #
# --------------------------------------------------------------------------- #


def _error_response(http_status: int, error_code: str, error_message: str) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content=ApiError.of(error_code, error_message).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning("[AppException] code=%s, message=%s", exc.code, exc.message)
        return _error_response(exc.http_status, exc.code, exc.message)

    @app.exception_handler(ExternalApiError)
    async def external_api_exception_handler(request: Request, exc: ExternalApiError) -> JSONResponse:
        logger.warning("[ExternalApiError] status=%s, message=%s", exc.status_code, exc.message)
        return _error_response(exc.status_code, "EXTERNAL_API_ERROR", exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        error_message = ", ".join(err.get("msg", "validation error") for err in exc.errors())
        logger.warning("[ValidationException] %s", error_message)
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY, VALIDATION_ERROR, error_message
        )

    @app.middleware("http")
    async def unhandled_exception_middleware(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error("[Exception]", exc_info=exc)
            return _error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, SERVER_ERROR, "서버 오류가 발생했습니다."
            )
