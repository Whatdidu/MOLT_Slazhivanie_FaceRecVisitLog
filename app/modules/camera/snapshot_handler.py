"""
Обработчик снапшотов с камеры.
Получает изображение, распознаёт лицо, логирует результат.
"""

import os
from datetime import datetime
from pathlib import Path

from app.core.logger import get_logger
from app.modules.recognition import get_recognition_service
from app.modules.recognition.models import EmployeeEmbedding
from app.modules.employees.crud import employee_crud
from app.db import get_session

logger = get_logger(__name__)


async def process_snapshot(file_path: str):
    """
    Обрабатывает снапшот с камеры.

    1. Читает изображение
    2. Запускает распознавание лица
    3. Логирует результат (match/unknown/no_face)
    4. Опционально: записывает в attendance

    Args:
        file_path: Путь к файлу снапшота
    """
    logger.info(f"Processing snapshot: {file_path}")

    try:
        # Читаем изображение
        with open(file_path, "rb") as f:
            image_data = f.read()

        if not image_data:
            logger.warning(f"Empty snapshot file: {file_path}")
            return

        # Получаем сервис распознавания
        recognition_service = get_recognition_service()

        if not recognition_service.is_ready():
            logger.warning("Recognition service not ready, skipping snapshot")
            return

        # Получаем сотрудников с эмбеддингами из БД
        async with get_session() as db:
            employees_with_embeddings = await employee_crud.get_employees_with_embeddings(db)

            if not employees_with_embeddings:
                logger.warning("No employees with embeddings in database")
                return

            # Конвертируем в формат для recognition service
            embeddings_db = [
                EmployeeEmbedding(
                    person_id=str(emp.id),
                    person_name=emp.full_name,
                    embedding=emb.vector
                )
                for emp, emb in employees_with_embeddings
                if emb.vector
            ]

            if not embeddings_db:
                logger.warning("No valid embeddings found")
                return

            # Распознаём лицо
            result = await recognition_service.recognize_face(image_data, embeddings_db)

            # Логируем результат
            _log_recognition_result(result, file_path)

            # TODO: Записать в attendance при match
            if result.status == "match" and result.person_id:
                logger.info(
                    f"ATTENDANCE: {result.person_name} (ID: {result.person_id}) "
                    f"detected at {datetime.now().isoformat()}"
                )
                # await _record_attendance(db, result.person_id)

    except FileNotFoundError:
        logger.error(f"Snapshot file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error processing snapshot {file_path}: {e}", exc_info=True)
    finally:
        # Опционально: удаляем обработанный файл
        # TODO: включить после отладки
        # _cleanup_snapshot(file_path)
        pass


def _log_recognition_result(result, file_path: str):
    """Логирует результат распознавания."""
    filename = Path(file_path).name

    if result.status == "match":
        logger.info(
            f"[MATCH] {result.person_name} "
            f"(confidence: {result.confidence:.2%}) "
            f"file: {filename}"
        )
    elif result.status == "low_confidence":
        logger.warning(
            f"[LOW_CONFIDENCE] Possible: {result.person_name} "
            f"(confidence: {result.confidence:.2%}) "
            f"file: {filename}"
        )
    elif result.status == "no_face":
        logger.info(f"[NO_FACE] No face detected in {filename}")
    elif result.status == "unknown":
        logger.info(f"[UNKNOWN] Unknown person in {filename}")
    else:
        logger.error(f"[ERROR] {result.error_message} file: {filename}")


def _cleanup_snapshot(file_path: str, keep_files: bool = False):
    """
    Удаляет обработанный снапшот.

    Args:
        file_path: Путь к файлу
        keep_files: Если True, файлы не удаляются (для отладки)
    """
    if keep_files:
        return

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up snapshot: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup snapshot {file_path}: {e}")
