"""
Lightweight провайдер на основе face_recognition (dlib).
Потребляет ~400-600 MB RAM вместо 2-2.5 GB у DeepFace.

Особенности:
- 128-мерные эмбеддинги (vs 512 у ArcFace)
- HOG детектор (быстрый, CPU-friendly)
- Подходит для серверов с ограниченной памятью (2-4 GB RAM)
"""

import asyncio
from typing import Any

import cv2
import numpy as np

from .base import BaseFaceProvider
from ..exceptions import ModelNotLoadedError, NoFaceDetectedError


class DlibFaceProvider(BaseFaceProvider):
    """
    Провайдер на основе face_recognition (dlib).

    Преимущества:
    - Низкое потребление RAM (~400-600 MB)
    - Быстрая работа на CPU
    - Простая установка

    Недостатки:
    - 128-dim эмбеддинги (vs 512 у ArcFace)
    - Чуть ниже точность на сложных случаях
    """

    def __init__(self):
        self._model_loaded = False
        self._face_recognition = None
        # HOG быстрее CNN, но чуть менее точен
        # Для офиса до 100 человек - достаточно
        self._detection_model = "hog"  # или "cnn" для GPU

    async def initialize(self) -> None:
        """Инициализация: импорт библиотеки."""
        if self._model_loaded:
            return

        await asyncio.get_event_loop().run_in_executor(
            None, self._load_models
        )

    def _load_models(self) -> None:
        """Синхронная загрузка моделей."""
        try:
            import face_recognition
            self._face_recognition = face_recognition

            # Прогрев модели - первый вызов загружает веса
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            self._face_recognition.face_locations(dummy_img, model=self._detection_model)

            self._model_loaded = True

        except ImportError as e:
            raise ModelNotLoadedError(
                f"face_recognition не установлен. "
                f"Установите: pip install face_recognition. Ошибка: {e}"
            )

    async def detect_faces(self, image: np.ndarray) -> list[dict[str, Any]]:
        """
        Детекция лиц на изображении.

        Returns:
            Список лиц: [{"bbox": (x, y, w, h), "confidence": float}, ...]
        """
        if not self._model_loaded:
            raise ModelNotLoadedError("Модель не загружена. Вызовите initialize()")

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._detect_faces_sync, image
        )
        return result

    def _detect_faces_sync(self, image: np.ndarray) -> list[dict[str, Any]]:
        """Синхронная детекция лиц."""
        # face_recognition работает с RGB, OpenCV дает BGR
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # face_locations возвращает (top, right, bottom, left)
        face_locations = self._face_recognition.face_locations(
            rgb_image,
            model=self._detection_model
        )

        detected = []
        for (top, right, bottom, left) in face_locations:
            # Конвертируем в формат (x, y, w, h)
            bbox = (left, top, right - left, bottom - top)
            detected.append({
                "bbox": bbox,
                # face_recognition не возвращает confidence,
                # но HOG детектор достаточно надёжен
                "confidence": 0.95
            })

        return detected

    async def extract_embedding(self, image: np.ndarray) -> list[float]:
        """
        Извлечение 128-мерного эмбеддинга лица.

        Returns:
            Список из 128 float значений
        """
        if not self._model_loaded:
            raise ModelNotLoadedError("Модель не загружена. Вызовите initialize()")

        result = await asyncio.get_event_loop().run_in_executor(
            None, self._extract_embedding_sync, image
        )
        return result

    def _extract_embedding_sync(self, image: np.ndarray) -> list[float]:
        """Синхронное извлечение эмбеддинга."""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Получаем эмбеддинги для всех лиц на изображении
        encodings = self._face_recognition.face_encodings(rgb_image)

        if encodings and len(encodings) > 0:
            # Возвращаем первый эмбеддинг (128-мерный numpy array)
            return encodings[0].tolist()

        # Если лицо не найдено, пробуем без детекции
        # (предполагаем, что изображение уже содержит только лицо)
        encodings = self._face_recognition.face_encodings(
            rgb_image,
            known_face_locations=[(0, image.shape[1], image.shape[0], 0)]
        )

        if encodings and len(encodings) > 0:
            return encodings[0].tolist()

        raise NoFaceDetectedError("Не удалось извлечь эмбеддинг: лицо не найдено")

    async def get_face_quality(self, image: np.ndarray) -> float:
        """
        Оценка качества лица.

        Факторы:
        - Размер лица относительно изображения
        - Чёткость (Лапласиан)
        - Наличие детекции

        Returns:
            Качество от 0.0 до 1.0
        """
        result = await asyncio.get_event_loop().run_in_executor(
            None, self._get_face_quality_sync, image
        )
        return result

    def _get_face_quality_sync(self, image: np.ndarray) -> float:
        """Синхронная оценка качества."""
        scores = []
        h, w = image.shape[:2]

        # 1. Размер изображения (минимум 100x100 для хорошего качества)
        size_score = min(1.0, (h * w) / (100 * 100))
        scores.append(size_score)

        # 2. Чёткость (Лапласиан)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 500)
        scores.append(sharpness_score)

        # 3. Детекция лица
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = self._face_recognition.face_locations(
            rgb_image,
            model=self._detection_model
        )

        if face_locations:
            # Лицо найдено
            scores.append(0.95)

            # Размер лица относительно изображения
            (top, right, bottom, left) = face_locations[0]
            face_area = (right - left) * (bottom - top)
            img_area = h * w
            face_ratio = face_area / img_area if img_area > 0 else 0
            face_size_score = min(1.0, face_ratio * 4)  # Оптимально 25%+ площади
            scores.append(face_size_score)
        else:
            scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def is_loaded(self) -> bool:
        """Проверка загружена ли модель."""
        return self._model_loaded

    @property
    def name(self) -> str:
        """Название провайдера."""
        return "Dlib (face_recognition)"

    @property
    def embedding_size(self) -> int:
        """Размерность эмбеддинга."""
        return 128


# Singleton для переиспользования загруженной модели
_provider_instance: DlibFaceProvider | None = None


def get_dlib_provider() -> DlibFaceProvider:
    """Получить singleton экземпляр провайдера."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = DlibFaceProvider()
    return _provider_instance
