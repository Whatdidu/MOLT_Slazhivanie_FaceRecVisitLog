"""
Модуль базы данных.

Поддерживает async операции (основной режим) и sync для совместимости.
"""

from app.db.models import Base, AttendanceLog, Employee, Embedding, EventType
from app.db.session import (
    engine,
    async_session_maker,
    init_db,
    close_db,
    get_session,
    get_db,
)

__all__ = [
    # Base
    "Base",
    # Models
    "AttendanceLog",
    "Employee",
    "Embedding",
    "EventType",
    # Session management
    "engine",
    "async_session_maker",
    "init_db",
    "close_db",
    "get_session",
    "get_db",
]
