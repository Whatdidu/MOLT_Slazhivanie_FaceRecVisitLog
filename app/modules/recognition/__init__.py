"""
Модуль распознавания лиц.

Публичный API для других модулей:
    - RecognitionService: главный сервис
    - get_recognition_service(): получить singleton
    - router: FastAPI роутер

Pydantic models:
    - RecognitionRequest, RecognitionResponse
    - EmbeddingResult, EmployeeEmbedding
"""

from .service import RecognitionService, get_recognition_service
from .router import router
from .models import (
    RecognitionRequest,
    RecognitionResponse,
    EmbeddingRequest,
    EmbeddingResult,
    CompareRequest,
    CompareResponse,
    HealthResponse,
    EmployeeEmbedding,
)
from .exceptions import (
    RecognitionError,
    NoFaceDetectedError,
    LowQualityImageError,
    InvalidImageError,
    ModelNotLoadedError,
    EmbeddingError,
)

__all__ = [
    # Service
    "RecognitionService",
    "get_recognition_service",
    "router",
    # Models
    "RecognitionRequest",
    "RecognitionResponse",
    "EmbeddingRequest",
    "EmbeddingResult",
    "CompareRequest",
    "CompareResponse",
    "HealthResponse",
    "EmployeeEmbedding",
    # Exceptions
    "RecognitionError",
    "NoFaceDetectedError",
    "LowQualityImageError",
    "InvalidImageError",
    "ModelNotLoadedError",
    "EmbeddingError",
]
