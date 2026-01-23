"""
Gateway API - Приемный шлюз для изображений от камеры.
Принимает снапшоты, валидирует и передает на распознавание.
"""

import uuid
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import get_logger
from app.db.session import get_db
from app.modules.recognition import get_recognition_service
from app.modules.recognition.models import EmployeeEmbedding
from app.modules.employees.crud import employee_crud
from app.modules.attendance.service import get_attendance_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/gateway", tags=["Gateway"])

# Константы валидации изображений
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MIN_IMAGE_WIDTH = 100
MIN_IMAGE_HEIGHT = 100


class SnapshotResponse(BaseModel):
    """Ответ на прием снапшота."""

    trace_id: str
    status: str
    message: str
    timestamp: datetime
    recognition_result: Optional[dict] = None


class ImageValidationError(BaseModel):
    """Ошибка валидации изображения."""

    trace_id: str
    error: str
    details: Optional[str] = None


def generate_trace_id() -> str:
    """Генерирует уникальный Trace ID для отслеживания запроса."""
    return str(uuid.uuid4())[:8]


def validate_content_type(content_type: Optional[str]) -> None:
    """Проверяет допустимость типа контента."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {content_type}. Allowed: {ALLOWED_CONTENT_TYPES}",
        )


async def validate_file_size(file: UploadFile) -> bytes:
    """Читает файл и проверяет размер."""
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)} MB",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file received",
        )

    return content


def validate_image_dimensions(image_bytes: bytes, trace_id: str) -> tuple[int, int]:
    """
    Проверяет минимальные размеры изображения.
    Возвращает (width, height).
    """
    try:
        # Пробуем определить размеры без PIL (базовая проверка заголовков)
        # Для JPEG
        if image_bytes[:2] == b"\xff\xd8":
            # Базовая проверка - файл является JPEG
            return (0, 0)  # Размеры будут проверены позже модулем recognition

        # Для PNG
        if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
            # PNG header содержит размеры в IHDR чанке
            width = int.from_bytes(image_bytes[16:20], "big")
            height = int.from_bytes(image_bytes[20:24], "big")

            if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image too small. Minimum: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}",
                )
            return (width, height)

        return (0, 0)  # Неизвестный формат - пропускаем проверку размеров

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[{trace_id}] Could not validate image dimensions: {e}")
        return (0, 0)


@router.post(
    "/snapshot",
    response_model=SnapshotResponse,
    responses={
        400: {"model": ImageValidationError, "description": "Invalid image"},
        413: {"model": ImageValidationError, "description": "File too large"},
        415: {"model": ImageValidationError, "description": "Unsupported media type"},
    },
)
async def receive_snapshot(
    request: Request,
    file: UploadFile = File(..., description="Изображение с камеры (JPEG/PNG)"),
    db: Session = Depends(get_db),
):
    """
    Принимает снапшот от камеры для распознавания.

    - Валидирует формат и размер изображения
    - Генерирует Trace ID для отслеживания
    - Передает изображение на распознавание (TODO)

    Returns:
        SnapshotResponse с результатом обработки
    """
    trace_id = generate_trace_id()
    timestamp = datetime.utcnow()

    logger.info(f"[{trace_id}] Received snapshot: {file.filename}, type: {file.content_type}")

    # Валидация типа контента
    validate_content_type(file.content_type)

    # Чтение и валидация размера файла
    image_bytes = await validate_file_size(file)

    # Валидация размеров изображения
    width, height = validate_image_dimensions(image_bytes, trace_id)

    logger.info(
        f"[{trace_id}] Image validated: size={len(image_bytes)} bytes, "
        f"dimensions={width}x{height}"
    )

    # 1. Получить все embeddings из БД
    embeddings_raw = employee_crud.get_all_embeddings(db)

    # 2. Конвертировать в формат для Recognition
    embeddings_db = []
    for emp_id, vector in embeddings_raw:
        # Получить имя сотрудника
        employee = employee_crud.get(db, emp_id)
        if employee:
            embeddings_db.append(
                EmployeeEmbedding(
                    person_id=emp_id,
                    person_name=employee.full_name,
                    embedding=vector
                )
            )

    logger.info(f"[{trace_id}] Loaded {len(embeddings_db)} embeddings from DB")

    # 3. Распознать лицо
    recognition_service = get_recognition_service()
    result = await recognition_service.recognize_face(image_bytes, embeddings_db)

    logger.info(
        f"[{trace_id}] Recognition completed: status={result.status}, "
        f"person_id={result.person_id}, confidence={result.confidence:.2f}"
    )

    # 4. Если найден сотрудник - записать в журнал
    if result.status == "match" and result.person_id:
        attendance_service = get_attendance_service()

        # Проверить анти-спам
        can_log = await attendance_service.can_log_entry(result.person_id)
        if can_log:
            # Записать вход
            await attendance_service.log_entry(
                employee_id=result.person_id,
                confidence=result.confidence,
                trace_id=trace_id
            )
            logger.info(f"[{trace_id}] Attendance logged for employee {result.person_id}")
        else:
            logger.info(
                f"[{trace_id}] Attendance not logged (cooldown active) "
                f"for employee {result.person_id}"
            )

    return SnapshotResponse(
        trace_id=trace_id,
        status=result.status,
        message=f"Recognition completed: {result.status}",
        timestamp=timestamp,
        recognition_result={
            "person_id": result.person_id,
            "person_name": result.person_name,
            "confidence": result.confidence,
        }
    )


@router.get("/health")
async def gateway_health():
    """Проверка работоспособности Gateway."""
    return {
        "status": "healthy",
        "service": "gateway",
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "allowed_types": list(ALLOWED_CONTENT_TYPES),
    }
