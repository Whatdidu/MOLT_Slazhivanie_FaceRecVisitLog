"""
Sputnik Face ID - Точка входа приложения.

Запуск:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup и shutdown события."""
    # Startup
    logger.info("Starting up application...")
    await init_db()

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()


# Создаём приложение
app = FastAPI(
    title="Sputnik Face ID",
    description="Система распознавания лиц для контроля посещаемости офиса",
    version="0.1.0",
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

# Подключаем роутеры
app.include_router(attendance_router)
app.include_router(admin_router)
app.include_router(employees_router)


@app.get("/")
async def root():
    """Корневой endpoint - редирект на админку."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin/")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "sputnik-face-id",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
