"""
Pydantic models для модуля распознавания лиц.
Определяет контракты API для взаимодействия с другими модулями.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
import uuid


class RecognitionRequest(BaseModel):
    """Запрос на распознавание лица."""
    image_base64: str = Field(..., description="Изображение в формате base64")
    camera_id: str = Field(default="main", description="ID камеры")
    trace_id: str | None = Field(default=None, description="ID для трассировки запроса")

    def get_trace_id(self) -> str:
        return self.trace_id or str(uuid.uuid4())


class RecognitionResponse(BaseModel):
    """Ответ распознавания."""
    status: Literal["match", "unknown", "low_confidence", "no_face", "error"]
    person_id: int | None = None
    person_name: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time_ms: int = Field(..., description="Время обработки в миллисекундах")
    trace_id: str
    error_message: str | None = None


class EmbeddingRequest(BaseModel):
    """Запрос на создание эмбеддинга."""
    image_base64: str = Field(..., description="Изображение в формате base64")


class EmbeddingResult(BaseModel):
    """Результат создания эмбеддинга."""
    embedding: list[float] = Field(..., description="512-мерный вектор лица")
    face_detected: bool = Field(..., description="Обнаружено ли лицо")
    face_quality: float = Field(default=0.0, ge=0.0, le=1.0, description="Качество лица 0-1")
    bbox: tuple[int, int, int, int] | None = Field(
        default=None,
        description="Координаты лица (x, y, width, height)"
    )


class CompareRequest(BaseModel):
    """Запрос на сравнение двух эмбеддингов."""
    embedding1: list[float]
    embedding2: list[float]


class CompareResponse(BaseModel):
    """Результат сравнения."""
    similarity: float = Field(..., ge=0.0, le=1.0, description="Схожесть 0-1")


class HealthResponse(BaseModel):
    """Ответ health check."""
    status: Literal["ok", "error"]
    model_loaded: bool
    version: str = "1.0.0"


class EmployeeEmbedding(BaseModel):
    """Эмбеддинг сотрудника из БД (используется при распознавании)."""
    person_id: int
    person_name: str
    embedding: list[float]
    created_at: datetime | None = None
