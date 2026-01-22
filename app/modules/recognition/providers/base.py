"""
Абстрактный базовый класс для ML-провайдеров распознавания лиц.
Позволяет легко переключаться между DeepFace, AWS Rekognition и др.
"""

from abc import ABC, abstractmethod
from typing import Any
import numpy as np


class BaseFaceProvider(ABC):
    """
    Абстрактный провайдер для работы с лицами.
    Реализации: DeepFaceProvider, AWSRekognitionProvider
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Инициализация провайдера (загрузка моделей)."""
        pass

    @abstractmethod
    async def detect_faces(self, image: np.ndarray) -> list[dict[str, Any]]:
        """
        Детекция лиц на изображении.

        Args:
            image: Изображение в формате numpy array (BGR)

        Returns:
            Список найденных лиц с координатами:
            [{"bbox": (x, y, w, h), "confidence": 0.99}, ...]
        """
        pass

    @abstractmethod
    async def extract_embedding(self, image: np.ndarray) -> list[float]:
        """
        Извлечение эмбеддинга лица.

        Args:
            image: Изображение с лицом (numpy array BGR)

        Returns:
            512-мерный вектор лица
        """
        pass

    @abstractmethod
    async def get_face_quality(self, image: np.ndarray) -> float:
        """
        Оценка качества лица на изображении.

        Args:
            image: Изображение с лицом

        Returns:
            Качество от 0.0 до 1.0
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Проверка загружена ли модель."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Название провайдера."""
        pass
