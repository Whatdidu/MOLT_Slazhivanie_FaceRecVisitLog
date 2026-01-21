"""
Обработка исключений и кастомные ошибки.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.logger import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ImageValidationError(AppException):
    """Ошибка валидации изображения."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class RecognitionError(AppException):
    """Ошибка распознавания лица."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class DatabaseError(AppException):
    """Ошибка базы данных."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class NotFoundError(AppException):
    """Ресурс не найден."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Обработчик AppException."""
    trace_id = getattr(request.state, "trace_id", "-")

    logger.error(
        f"AppException: {exc.message}",
        extra={"trace_id": trace_id},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "trace_id": trace_id,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Обработчик HTTPException."""
    trace_id = getattr(request.state, "trace_id", "-")

    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={"trace_id": trace_id},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "trace_id": trace_id,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик непредвиденных исключений."""
    trace_id = getattr(request.state, "trace_id", "-")

    logger.exception(
        f"Unhandled exception: {str(exc)}",
        extra={"trace_id": trace_id},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "trace_id": trace_id,
        },
    )
