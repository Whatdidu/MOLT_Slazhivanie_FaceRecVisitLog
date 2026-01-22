"""
Sputnik Face ID - Точка входа приложения.
FastAPI приложение для системы распознавания лиц.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logger import get_logger, setup_logging
from app.core.middleware import TraceIDMiddleware
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.api.gateway import router as gateway_router
from app.modules.employees import router as employees_router
from app.db import init_db, close_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для приложения."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Система распознавания лиц для контроля посещаемости офиса",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Trace ID Middleware (должен быть добавлен первым)
app.add_middleware(TraceIDMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (debug photos)
app.mount("/static", StaticFiles(directory=settings.static_path), name="static")


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/v1/info", tags=["System"])
async def get_info():
    """Информация о сервисе."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }


# Gateway router (прием изображений от камеры)
app.include_router(gateway_router)

# Employees router (управление сотрудниками)
app.include_router(employees_router)

# TODO: Подключение остальных роутеров модулей (будут добавлены по мере реализации)
# from app.modules.recognition.router import router as recognition_router
# from app.modules.attendance.router import router as attendance_router
#
# app.include_router(recognition_router, prefix="/api/v1/recognition", tags=["Recognition"])
# app.include_router(attendance_router, prefix="/api/v1/attendance", tags=["Attendance"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
