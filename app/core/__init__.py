"""
Core module - конфигурация, логирование, утилиты.
"""

from app.core.config import Settings, get_settings, settings
from app.core.constants import (
    API_V1_PREFIX,
    ATTENDANCE_MIN_INTERVAL_SECONDS,
    DEBUG_PHOTOS_TTL_DAYS,
    MAX_IMAGE_SIZE_BYTES,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    RECOGNITION_LOW_CONFIDENCE_THRESHOLD,
    RECOGNITION_MATCH_THRESHOLD,
    RecognitionStatus,
)
from app.core.exceptions import (
    AppException,
    DatabaseError,
    ImageValidationError,
    NotFoundError,
    RecognitionError,
)
from app.core.logger import get_logger, setup_logging
from app.core.middleware import TraceIDMiddleware
from app.core.trace import generate_trace_id, get_trace_id, set_trace_id

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "settings",
    # Logger
    "get_logger",
    "setup_logging",
    # Middleware
    "TraceIDMiddleware",
    # Trace
    "generate_trace_id",
    "get_trace_id",
    "set_trace_id",
    # Constants
    "API_V1_PREFIX",
    "ATTENDANCE_MIN_INTERVAL_SECONDS",
    "DEBUG_PHOTOS_TTL_DAYS",
    "MAX_IMAGE_SIZE_BYTES",
    "MIN_IMAGE_HEIGHT",
    "MIN_IMAGE_WIDTH",
    "RECOGNITION_LOW_CONFIDENCE_THRESHOLD",
    "RECOGNITION_MATCH_THRESHOLD",
    "RecognitionStatus",
    # Exceptions
    "AppException",
    "DatabaseError",
    "ImageValidationError",
    "NotFoundError",
    "RecognitionError",
]
