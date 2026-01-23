"""
Конфигурация приложения через переменные окружения.
Использует Pydantic Settings для валидации и типизации.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из .env файла."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "SputnikFaceID"
    app_version: str = "0.1.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/sputnik_faceid"
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "sputnik"
    db_password: str = "sputnik_password"
    db_name: str = "sputnik_faceid"

    # Logging
    log_level: str = "INFO"

    # Storage
    static_path: str = "app/static"
    debug_photos_ttl_days: int = 7

    # Recognition thresholds
    recognition_match_threshold: float = 0.55
    recognition_low_confidence_threshold: float = 0.40

    # Recognition provider: "dlib" or "mock"
    # - dlib: lightweight, ~500 MB RAM (рекомендуется для серверов с 2 GB)
    # - mock: без ML, для тестирования
    recognition_provider: str = "dlib"


@lru_cache
def get_settings() -> Settings:
    """
    Возвращает singleton экземпляр настроек.
    Кэшируется для повторного использования.
    """
    return Settings()


settings = get_settings()
