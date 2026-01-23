"""
ML провайдеры для распознавания лиц.

Доступные провайдеры:
- DlibFaceProvider: face_recognition/dlib (lightweight, ~500 MB RAM)
- BaseFaceProvider: Абстрактный базовый класс

Выбор провайдера через переменную окружения RECOGNITION_PROVIDER:
- "dlib" (по умолчанию) — для серверов с 2 GB RAM
- "mock" — без ML, для тестирования
"""

from .base import BaseFaceProvider
from .dlib_provider import DlibFaceProvider, get_dlib_provider

__all__ = [
    "BaseFaceProvider",
    "DlibFaceProvider",
    "get_dlib_provider",
]
