"""
Sputnik Face ID - Точка входа приложения.
FastAPI приложение для системы распознавания лиц.

Запуск:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logger import get_logger, setup_logging
from app.core.middleware import TraceIDMiddleware, AuthMiddleware
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from app.core.tasks import start_background_tasks, stop_background_tasks
from app.core.storage import get_storage_manager
from app.modules.attendance.router import router as attendance_router
from app.modules.admin.router import router as admin_router
from app.modules.employees.router import router as employees_router
from app.modules.recognition.router import router as recognition_router
from app.modules.showcase.router import router as showcase_router
from app.api.gateway import router as gateway_router
from app.db import init_db, close_db
from app.modules.recognition import init_recognition_service
from app.modules.camera import start_ftp_server, stop_ftp_server, process_snapshot

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для приложения."""
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")

    # Initialize storage directories
    storage_manager = get_storage_manager()
    logger.info("Storage directories initialized")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize recognition service
    try:
        recognition_service = await init_recognition_service()
        if recognition_service.is_ready():
            logger.info("✅ Recognition service initialized successfully")
        else:
            logger.warning("⚠️ Recognition service not ready (mock mode)")
    except Exception as e:
        logger.error(f"Failed to initialize recognition service: {e}")
        logger.warning("Application will continue with limited functionality")

    # Start background tasks (cleanup scheduler)
    await start_background_tasks()
    logger.info("Background tasks started")

    # Start FTP server for camera snapshots
    try:
        await start_ftp_server(on_file_callback=process_snapshot)
        logger.info("FTP server for camera snapshots started")
    except Exception as e:
        logger.error(f"Failed to start FTP server: {e}")
        logger.warning("Application will continue without FTP server")

    yield

    # Shutdown
    logger.info("Shutting down application")

    # Stop FTP server
    await stop_ftp_server()
    logger.info("FTP server stopped")

    # Stop background tasks
    await stop_background_tasks()
    logger.info("Background tasks stopped")

    await close_db()
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

# Auth Middleware для защиты админки
app.add_middleware(AuthMiddleware)

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

# Snapshots directory for viewing camera snapshots (html=True enables directory listing)
app.mount("/snapshots", StaticFiles(directory=settings.ftp_snapshots_dir, html=True), name="snapshots")


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Корневой endpoint - редирект на админку."""
    return RedirectResponse(url="/admin/")


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


# Подключаем роутеры
app.include_router(attendance_router)
app.include_router(admin_router)
app.include_router(employees_router)
app.include_router(recognition_router)
app.include_router(gateway_router)
app.include_router(showcase_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
