"""
Sputnik Face ID - Точка входа приложения.

Запуск:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db, close_db
from app.modules.attendance.router import router as attendance_router
from app.modules.admin.router import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: startup и shutdown события."""
    # Startup
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    await close_db()
    print("👋 Database connection closed")


# Создаём приложение
app = FastAPI(
    title="Sputnik Face ID",
    description="Система распознавания лиц для контроля посещаемости офиса",
    version="0.1.0",
    lifespan=lifespan,
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Подключаем роутеры
app.include_router(attendance_router)
app.include_router(admin_router)


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
