"""
Настройка логирования для приложения.
Поддерживает форматирование с Trace ID для сквозного отслеживания запросов.
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


class TraceIDFilter(logging.Filter):
    """Фильтр для добавления trace_id в записи логов."""

    def __init__(self, default_trace_id: str = "-"):
        super().__init__()
        self.default_trace_id = default_trace_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = self.default_trace_id
        return True


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Настраивает логирование для всего приложения.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Если не указан, берется из настроек.
    """
    level = log_level or settings.log_level

    # Формат логов: время | уровень | trace_id | модуль | сообщение
    log_format = "%(asctime)s | %(levelname)-8s | %(trace_id)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Настройка root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Удаляем существующие handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    console_handler.addFilter(TraceIDFilter())

    root_logger.addHandler(console_handler)

    # Уменьшаем уровень логов для сторонних библиотек
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает логгер с указанным именем.

    Args:
        name: Имя логгера (обычно __name__ модуля).

    Returns:
        Настроенный логгер.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", extra={"trace_id": "abc123"})
    """
    logger = logging.getLogger(name)
    return logger


# Инициализация логирования при импорте модуля
setup_logging()
