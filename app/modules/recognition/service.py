"""
Главный сервис распознавания лиц.
Оркестрирует работу провайдеров и предоставляет API для других модулей.
"""

import base64
import time
from typing import Sequence

import numpy as np

from .models import (
    EmbeddingResult,
    RecognitionResponse,
    EmployeeEmbedding,
)
from .embeddings import cosine_similarity, find_best_match
from .exceptions import (
    InvalidImageError,
    NoFaceDetectedError,
    ModelNotLoadedError,
)
from .providers.base import BaseFaceProvider


# Пороги уверенности (для Euclidean distance: confidence = 1 - distance)
# distance < 0.4 → confidence > 0.6 → "match"
# distance 0.4-0.6 → confidence 0.4-0.6 → "low_confidence"
# distance > 0.6 → confidence < 0.4 → "unknown"
THRESHOLD_MATCH = 0.60
THRESHOLD_LOW_CONFIDENCE = 0.40

# Порог евклидова расстояния (стандарт для dlib: 0.6)
DISTANCE_THRESHOLD = 0.6


class RecognitionService:
    """
    Главный сервис распознавания.
    Используется модулями employees и attendance.
    """

    def __init__(self, provider: BaseFaceProvider | None = None):
        self._provider = provider
        self._is_initialized = False

    async def initialize(self) -> None:
        """Инициализация сервиса и загрузка моделей."""
        if self._provider:
            await self._provider.initialize()
        self._is_initialized = True

    def is_ready(self) -> bool:
        """Проверка готовности сервиса."""
        if self._provider:
            return self._provider.is_loaded()
        return self._is_initialized

    async def create_embedding(self, image: bytes) -> EmbeddingResult:
        """
        Создаёт вектор лица из изображения.
        Вызывается: employees (при регистрации сотрудника)

        Args:
            image: Изображение в байтах (JPEG/PNG)

        Returns:
            EmbeddingResult с эмбеддингом и метаданными
        """
        img_array = self._decode_image(image)

        if self._provider is None:
            return self._mock_embedding_result()

        faces = await self._provider.detect_faces(img_array)
        if not faces:
            return EmbeddingResult(
                embedding=[],
                face_detected=False,
                face_quality=0.0,
                bbox=None,
            )

        face = faces[0]
        bbox = face.get("bbox", (0, 0, 0, 0))

        embedding = await self._provider.extract_embedding(img_array)
        quality = await self._provider.get_face_quality(img_array)

        return EmbeddingResult(
            embedding=embedding,
            face_detected=True,
            face_quality=quality,
            bbox=bbox,
        )

    async def recognize_face(
        self,
        image: bytes,
        embeddings_db: list[EmployeeEmbedding],
    ) -> RecognitionResponse:
        """
        Распознаёт лицо, сравнивая с базой.
        Вызывается: main.py (при получении кадра с камеры)

        Args:
            image: Изображение в байтах
            embeddings_db: Список эмбеддингов сотрудников из БД

        Returns:
            RecognitionResponse со статусом и данными
        """
        import uuid
        trace_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        try:
            embedding_result = await self.create_embedding(image)

            if not embedding_result.face_detected:
                return RecognitionResponse(
                    status="no_face",
                    processing_time_ms=self._calc_time_ms(start_time),
                    trace_id=trace_id,
                )

            db_tuples = [
                (e.person_id, e.person_name, e.embedding)
                for e in embeddings_db
            ]

            person_id, person_name, similarity = find_best_match(
                embedding_result.embedding,
                db_tuples,
                threshold=DISTANCE_THRESHOLD,
            )

            status = self._determine_status(similarity)

            return RecognitionResponse(
                status=status,
                person_id=person_id if status != "unknown" else None,
                person_name=person_name if status != "unknown" else None,
                confidence=similarity,
                processing_time_ms=self._calc_time_ms(start_time),
                trace_id=trace_id,
            )

        except Exception as e:
            return RecognitionResponse(
                status="error",
                processing_time_ms=self._calc_time_ms(start_time),
                trace_id=trace_id,
                error_message=str(e),
            )

    async def compare_faces(
        self,
        embedding1: Sequence[float],
        embedding2: Sequence[float],
    ) -> float:
        """
        Сравнивает два вектора.

        Returns:
            similarity: float 0.0-1.0 (cosine similarity)
        """
        return cosine_similarity(embedding1, embedding2)

    def _decode_image(self, image_data: bytes) -> np.ndarray:
        """Декодирует изображение из байтов в numpy array."""
        import cv2
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise InvalidImageError("Не удалось декодировать изображение")
        return img

    def _determine_status(self, similarity: float) -> str:
        """Определяет статус по уровню схожести."""
        if similarity >= THRESHOLD_MATCH:
            return "match"
        elif similarity >= THRESHOLD_LOW_CONFIDENCE:
            return "low_confidence"
        return "unknown"

    def _calc_time_ms(self, start_time: float) -> int:
        """Вычисляет время обработки в мс."""
        return int((time.perf_counter() - start_time) * 1000)

    def _mock_embedding_result(self) -> EmbeddingResult:
        """Mock результат для тестирования без ML модели."""
        return EmbeddingResult(
            embedding=[0.1] * 512,
            face_detected=True,
            face_quality=0.85,
            bbox=(100, 100, 200, 200),
        )


# Singleton instance
_recognition_service: RecognitionService | None = None


def get_recognition_service(provider_name: str | None = None) -> RecognitionService:
    """
    Получить singleton экземпляр сервиса.

    Args:
        provider_name: Название провайдера ("dlib", "mock").
                      Если None — берётся из конфига RECOGNITION_PROVIDER.

    Returns:
        RecognitionService с настроенным провайдером
    """
    global _recognition_service
    if _recognition_service is None:
        # Получаем провайдер из конфига, если не указан явно
        if provider_name is None:
            from app.core.config import settings
            provider_name = getattr(settings, 'recognition_provider', 'dlib')

        provider = _create_provider(provider_name)
        _recognition_service = RecognitionService(provider=provider)

    return _recognition_service


def _create_provider(provider_name: str):
    """
    Создаёт провайдер по имени.

    Args:
        provider_name: "dlib" или "mock"

    Returns:
        Экземпляр провайдера или None для mock режима
    """
    provider_name = provider_name.lower()

    if provider_name == "mock":
        return None

    if provider_name == "dlib":
        try:
            from .providers.dlib_provider import get_dlib_provider
            return get_dlib_provider()
        except ImportError as e:
            import logging
            logging.warning(f"face_recognition не установлен: {e}. Используем mock режим.")
            return None

    # Неизвестный провайдер — mock
    import logging
    logging.warning(f"Неизвестный провайдер: {provider_name}. Используем mock режим.")
    return None


async def init_recognition_service(provider_name: str | None = None) -> RecognitionService:
    """
    Инициализировать сервис распознавания (загрузить модели).

    Args:
        provider_name: Название провайдера ("dlib", "mock").
                      Если None — берётся из конфига RECOGNITION_PROVIDER.

    Вызывать при старте приложения (lifespan).
    """
    service = get_recognition_service(provider_name=provider_name)
    await service.initialize()
    return service
