"""
Sputnik Face ID - Точка входа приложения.
FastAPI приложение для системы распознавания лиц.

Запуск:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.db import init_db, close_db
from app.modules.attendance.router import router as attendance_router
from app.modules.admin.router import router as admin_router
from app.modules.employees.router import router as employees_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# App settings
APP_NAME = "Sputnik Face ID"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup и shutdown события."""
    # Startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Debug mode: {DEBUG}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Система распознавания лиц для контроля посещаемости офиса",
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")


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
        "app_name": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/api/v1/info", tags=["System"])
async def get_info():
    """Информация о сервисе."""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "debug": DEBUG,
    }


# Подключаем роутеры
app.include_router(attendance_router)
app.include_router(admin_router)
app.include_router(employees_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=DEBUG
    )
