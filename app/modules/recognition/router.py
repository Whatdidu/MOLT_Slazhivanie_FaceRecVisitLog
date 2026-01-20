"""
FastAPI роутер для модуля распознавания.
Эндпоинты: /api/v1/recognition/*
"""

import base64
from fastapi import APIRouter, HTTPException

from .models import (
    RecognitionRequest,
    RecognitionResponse,
    EmbeddingRequest,
    EmbeddingResult,
    CompareRequest,
    CompareResponse,
    HealthResponse,
)
from .service import get_recognition_service
from .exceptions import InvalidImageError, RecognitionError


router = APIRouter(prefix="/api/v1/recognition", tags=["recognition"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка состояния сервиса распознавания."""
    service = get_recognition_service()
    return HealthResponse(
        status="ok" if service.is_ready() else "error",
        model_loaded=service.is_ready(),
    )


@router.post("/detect", response_model=RecognitionResponse)
async def detect_face(request: RecognitionRequest):
    """
    Распознать лицо на изображении.

    Сравнивает с базой сотрудников и возвращает результат:
    - match: лицо распознано (confidence >= 0.55)
    - low_confidence: низкая уверенность (0.40 - 0.55)
    - unknown: не найдено в базе
    - no_face: лицо не обнаружено
    - error: ошибка обработки
    """
    service = get_recognition_service()

    try:
        image_bytes = base64.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Невалидный base64")

    # TODO: Получить embeddings_db из модуля employees
    embeddings_db = []

    result = await service.recognize_face(image_bytes, embeddings_db)
    return result


@router.post("/embedding", response_model=EmbeddingResult)
async def create_embedding(request: EmbeddingRequest):
    """
    Создать эмбеддинг (вектор) лица.

    Используется при регистрации нового сотрудника.
    Возвращает 512-мерный вектор для сохранения в БД.
    """
    service = get_recognition_service()

    try:
        image_bytes = base64.b64decode(request.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Невалидный base64")

    try:
        result = await service.create_embedding(image_bytes)
        return result
    except InvalidImageError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RecognitionError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=CompareResponse)
async def compare_embeddings(request: CompareRequest):
    """
    Сравнить два эмбеддинга.

    Возвращает similarity от 0.0 до 1.0.
    """
    service = get_recognition_service()
    similarity = await service.compare_faces(request.embedding1, request.embedding2)
    return CompareResponse(similarity=similarity)
