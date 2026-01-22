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


logger = logging.getLogger(__name__)

# Получаем URL базы данных из переменных окружения
# По умолчанию используем SQLite для разработки
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/attendance.db"
)

# Для PostgreSQL URL будет выглядеть так:
# DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/dbname"


# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
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
        logger.info("✅ Database initialized")
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
