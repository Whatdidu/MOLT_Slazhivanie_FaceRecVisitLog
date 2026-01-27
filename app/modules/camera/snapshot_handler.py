"""
Обработчик снапшотов с камеры.
Получает изображение, распознаёт лицо, логирует результат.
"""

import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.core.logger import get_logger
from app.modules.recognition import get_recognition_service
from app.modules.recognition.models import EmployeeEmbedding
from app.modules.employees.crud import employee_crud
from app.modules.attendance.service import get_attendance_service
from app.db import get_session
from app.core.config import settings

logger = get_logger(__name__)

# Семафор для ограничения параллельной обработки снапшотов
# Максимум 5 одновременных обработок, чтобы не перегружать БД
_processing_semaphore = asyncio.Semaphore(5)

# Таблица транслитерации кириллицы в латиницу
_TRANSLIT_TABLE = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    ' ': '_',
}


def transliterate(text: str) -> str:
    """Транслитерирует кириллицу в латиницу."""
    result = []
    for char in text:
        result.append(_TRANSLIT_TABLE.get(char, char))
    return ''.join(result)


async def process_snapshot(file_path: str):
    """
    Обрабатывает снапшот с камеры.

    1. Читает изображение
    2. Запускает распознавание лица
    3. Логирует результат (match/unknown/no_face)
    4. Обрабатывает файл в зависимости от результата:
       - MATCH: переименовывает и перемещает в /recognized/
       - UNKNOWN/LOW_CONFIDENCE: оставляет как есть
       - NO_FACE: удаляет

    Args:
        file_path: Путь к файлу снапшота
    """
    # Ограничиваем параллельную обработку через семафор
    async with _processing_semaphore:
        await _process_snapshot_internal(file_path)


async def _process_snapshot_internal(file_path: str):
    """Внутренняя функция обработки снапшота."""
    logger.info(f"Processing snapshot: {file_path}")

    try:
        # Читаем изображение
        with open(file_path, "rb") as f:
            image_data = f.read()

        if not image_data:
            logger.warning(f"Empty snapshot file: {file_path}")
            _delete_snapshot(file_path)
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

            # Обрабатываем файл в зависимости от результата
            if result.status == "match" and result.person_id:
                # Записываем в attendance
                await _record_attendance(
                    employee_id=int(result.person_id),
                    confidence=result.confidence,
                    trace_id=Path(file_path).stem,
                )
                # Перемещаем в папку recognized с новым именем
                _move_to_recognized(file_path, result.person_name, result.confidence)

            elif result.status == "no_face":
                # Удаляем фото без лица
                _delete_snapshot(file_path)

            # UNKNOWN и LOW_CONFIDENCE - оставляем как есть для анализа


    except FileNotFoundError:
        logger.error(f"Snapshot file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error processing snapshot {file_path}: {e}", exc_info=True)


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


async def _record_attendance(employee_id: int, confidence: float, trace_id: str):
    """
    Записывает посещение в базу данных.

    Args:
        employee_id: ID сотрудника
        confidence: Уверенность распознавания
        trace_id: Уникальный ID для отслеживания (имя файла снапшота)
    """
    attendance_service = get_attendance_service()

    # Проверяем анти-спам (не более 1 записи в 5 минут)
    can_log = await attendance_service.can_log_entry(employee_id)

    if not can_log:
        logger.debug(f"Skipping attendance log for employee {employee_id} (cooldown)")
        return

    try:
        log_entry = await attendance_service.log_entry(
            employee_id=employee_id,
            confidence=confidence,
            trace_id=trace_id,
        )
        logger.info(
            f"ATTENDANCE RECORDED: {log_entry.employee_name} (ID: {employee_id}) "
            f"at {log_entry.timestamp.isoformat()} [confidence: {confidence:.2%}]"
        )
    except Exception as e:
        logger.error(f"Failed to record attendance for employee {employee_id}: {e}")


def _move_to_recognized(file_path: str, person_name: str, confidence: float):
    """
    Перемещает распознанный снапшот в папку recognized.

    Args:
        file_path: Исходный путь к файлу
        person_name: Имя распознанного сотрудника
        confidence: Уверенность распознавания
    """
    try:
        # Создаём папку recognized
        recognized_dir = Path(settings.ftp_snapshots_dir) / "recognized"
        recognized_dir.mkdir(parents=True, exist_ok=True)

        # Формируем новое имя файла: Imya_Familiya_20260127_143052_58.jpg
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        confidence_pct = int(confidence * 100)
        name_translit = transliterate(person_name)
        new_filename = f"{name_translit}_{timestamp}_{confidence_pct}.jpg"

        new_path = recognized_dir / new_filename

        # Перемещаем файл
        shutil.move(file_path, new_path)
        logger.info(f"Moved recognized snapshot to: {new_path}")

    except Exception as e:
        logger.error(f"Failed to move snapshot {file_path}: {e}")


def _delete_snapshot(file_path: str):
    """Удаляет снапшот."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted snapshot: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete snapshot {file_path}: {e}")
