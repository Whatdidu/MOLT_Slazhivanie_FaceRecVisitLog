"""
Модуль учёта посещаемости (Attendance).

Отвечает за:
- Журнал посещений (логирование входов/выходов)
- Анти-спам фильтрация
- Статусы присутствия сотрудников
- Отчёты и экспорт данных
"""

from app.modules.attendance.service import AttendanceService, get_attendance_service
from app.modules.attendance.router import router

__all__ = [
    "AttendanceService",
    "get_attendance_service",
    "router",
]
