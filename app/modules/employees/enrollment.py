"""
Сервис регистрации сотрудников (Enrollment).

Процесс:
1. Загрузка фото сотрудника
2. Извлечение face embedding через Recognition
3. Сохранение Employee + Embedding в БД
4. Удаление временного фото
"""

import os
import uuid
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.db.models import Employee, Embedding


# Директория для временных фото
PHOTOS_DIR = Path("app/static/employees")
PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


class EnrollmentService:
    """Сервис регистрации сотрудников с фото."""

    async def enroll(
        self,
        full_name: str,
        photo: UploadFile,
        email: Optional[str] = None,
        department: Optional[str] = None,
    ) -> dict:
        """
        Зарегистрировать нового сотрудника.

        Args:
            full_name: Полное имя сотрудника
            photo: Файл фото
            email: Email (опционально)
            department: Отдел (опционально)

        Returns:
            Словарь с данными сотрудника и embedding
        """
        # 1. Сохраняем фото временно
        photo_path = await self._save_photo(photo)

        try:
            # 2. Получаем face embedding
            vector = await self._get_face_embedding(photo_path)

            if vector is None:
                # Удаляем фото если лицо не найдено
                self._delete_photo(photo_path)
                raise ValueError("Лицо не обнаружено на фото. Загрузите другое фото.")

            # 3. Сохраняем в БД
            async with get_session() as session:
                # Создаём сотрудника
                employee = Employee(
                    full_name=full_name,
                    email=email,
                    department=department,
                    photo_path=str(photo_path),
                    is_active=True,
                )
                session.add(employee)
                await session.flush()

                # Сохраняем embedding
                embedding = Embedding(
                    employee_id=employee.id,
                    vector=vector,
                    model_version="dlib-face_recognition-1.3.0",
                )
                session.add(embedding)
                await session.flush()

                result = {
                    "employee": {
                        "id": employee.id,
                        "full_name": employee.full_name,
                        "email": employee.email,
                        "department": employee.department,
                        "photo_path": employee.photo_path,
                        "created_at": employee.created_at.isoformat() if employee.created_at else None,
                    },
                    "embedding": {
                        "id": embedding.id,
                        "vector_dim": len(vector),
                        "model_version": embedding.model_version,
                    },
                    "message": "Сотрудник успешно зарегистрирован",
                }

            return result

        except Exception as e:
            # При ошибке удаляем фото
            self._delete_photo(photo_path)
            raise

    async def _save_photo(self, photo: UploadFile) -> Path:
        """Сохранить загруженное фото."""
        # Генерируем уникальное имя файла
        ext = Path(photo.filename).suffix if photo.filename else ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = PHOTOS_DIR / filename

        # Сохраняем файл
        content = await photo.read()
        with open(filepath, "wb") as f:
            f.write(content)

        return filepath

    def _delete_photo(self, photo_path: Path):
        """Удалить временное фото."""
        try:
            if photo_path.exists():
                photo_path.unlink()
        except Exception:
            pass  # Игнорируем ошибки удаления

    async def _get_face_embedding(self, photo_path: Path) -> Optional[List[float]]:
        """
        Получить face embedding из фото через Recognition сервис.
        """
        from app.modules.recognition import get_recognition_service

        # Читаем фото
        with open(photo_path, 'rb') as f:
            image_bytes = f.read()

        # Создаём embedding через Recognition сервис
        recognition_service = get_recognition_service()
        result = await recognition_service.create_embedding(image_bytes)

        if not result.face_detected:
            return None

        if result.face_quality < 0.3:  # Минимальный порог качества
            return None

        return result.embedding

    def _vector_to_blob(self, vector: List[float]) -> bytes:
        """Конвертировать вектор в бинарный формат."""
        return struct.pack(f'{len(vector)}f', *vector)

    def _blob_to_vector(self, blob: bytes) -> List[float]:
        """Конвертировать бинарные данные в вектор."""
        count = len(blob) // 4  # 4 bytes per float
        return list(struct.unpack(f'{count}f', blob))

    async def get_all_embeddings(self) -> List[tuple]:
        """
        Получить все embeddings для распознавания.

        Returns:
            Список кортежей (employee_id, vector)
        """
        async with get_session() as session:
            result = await session.execute(
                select(Embedding, Employee)
                .join(Employee)
                .where(Employee.is_active == True)
            )
            rows = result.all()

            return [
                (row.Embedding.employee_id, row.Embedding.vector)
                for row in rows
            ]

    async def find_match(self, vector: List[float], threshold: float = 0.6) -> Optional[dict]:
        """
        Найти сотрудника по face embedding.

        Args:
            vector: Вектор лица для поиска
            threshold: Минимальный порог сходства (0-1)

        Returns:
            Данные сотрудника или None
        """
        embeddings = await self.get_all_embeddings()

        if not embeddings:
            return None

        best_match = None
        best_score = threshold

        for employee_id, stored_vector in embeddings:
            score = self._cosine_similarity(vector, stored_vector)
            if score > best_score:
                best_score = score
                best_match = employee_id

        if best_match:
            async with get_session() as session:
                result = await session.execute(
                    select(Employee).where(Employee.id == best_match)
                )
                employee = result.scalar_one_or_none()
                if employee:
                    return {
                        "employee_id": employee.id,
                        "full_name": employee.full_name,
                        "confidence": best_score,
                    }

        return None

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Вычислить косинусное сходство двух векторов."""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a**2 for a in v1) ** 0.5
        norm2 = sum(b**2 for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


# Singleton
enrollment_service = EnrollmentService()
