"""
Настройка подключения к базе данных.

Поддерживает async операции через aiosqlite/asyncpg.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.models import Base
from app.core.config import settings


logger = logging.getLogger(__name__)

# Определяем URL базы данных
# Для разработки используем SQLite, для продакшена - PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/attendance.db"
)

# Если указан PostgreSQL URL, конвертируем в async версию
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


# Создаём асинхронный движок с увеличенным пулом соединений
# pool_size=20 - базовый размер пула
# max_overflow=30 - дополнительные соединения при пиковой нагрузке
# pool_timeout=60 - таймаут ожидания соединения
# pool_recycle=1800 - пересоздание соединений каждые 30 минут
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_size=20,
    max_overflow=30,
    pool_timeout=60,
    pool_recycle=1800,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Инициализация базы данных (создание таблиц)."""
    logger.info("Initializing database...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Закрытие соединений с БД."""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекстный менеджер для получения сессии БД.

    Usage:
        async with get_session() as session:
            result = await session.execute(query)
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI.

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
