"""
Middleware для FastAPI приложения.
"""

import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.logger import get_logger

logger = get_logger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware для добавления Trace ID к каждому запросу.
    Trace ID используется для сквозного отслеживания запроса через все сервисы.
    """

    async def dispatch(self, request: Request, call_next):
        # Получаем trace_id из заголовка или генерируем новый
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())[:8]

        # Сохраняем в state для использования в handlers
        request.state.trace_id = trace_id

        # Логируем начало запроса
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={"trace_id": trace_id},
        )

        # Выполняем запрос
        response = await call_next(request)

        # Логируем завершение запроса
        process_time = time.time() - start_time
        logger.info(
            f"Request completed: {response.status_code} in {process_time:.3f}s",
            extra={"trace_id": trace_id},
        )

        # Добавляем trace_id в заголовки ответа
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response
