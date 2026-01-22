"""
Кастомные исключения модуля распознавания.
"""


class RecognitionError(Exception):
    """Базовое исключение модуля распознавания."""
    pass


class NoFaceDetectedError(RecognitionError):
    """Лицо не обнаружено на изображении."""
    pass


class LowQualityImageError(RecognitionError):
    """Качество изображения слишком низкое."""
    pass


class ModelNotLoadedError(RecognitionError):
    """ML модель не загружена."""
    pass


class InvalidImageError(RecognitionError):
    """Невалидное изображение (не удалось декодировать)."""
    pass


class EmbeddingError(RecognitionError):
    """Ошибка при создании эмбеддинга."""
    pass
