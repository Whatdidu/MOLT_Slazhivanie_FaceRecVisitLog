"""
Pydantic модели для модуля Attendance.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Тип события посещения."""
    ENTRY = "entry"
    EXIT = "exit"


class PresenceStatus(str, Enum):
    """Статус присутствия сотрудника."""
    IN_OFFICE = "in_office"
    LEFT = "left"
    UNKNOWN = "unknown"


# ============== Request Models ==============

class AttendanceLogRequest(BaseModel):
    """Запрос на создание записи в журнале."""
    employee_id: int = Field(..., description="ID сотрудника")
    event_type: EventType = Field(default=EventType.ENTRY, description="Тип события")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность распознавания")
    trace_id: str = Field(..., description="Сквозной ID для логирования")


class AttendanceHistoryRequest(BaseModel):
    """Параметры запроса истории посещений."""
    start_date: date = Field(..., description="Начало периода")
    end_date: date = Field(..., description="Конец периода")
    employee_id: Optional[int] = Field(None, description="Фильтр по сотруднику")
    department: Optional[str] = Field(None, description="Фильтр по отделу")


class ExportRequest(BaseModel):
    """Параметры экспорта данных."""
    start_date: date
    end_date: date
    employee_id: Optional[int] = None
    format: str = Field(default="json", pattern="^(json|excel)$")


# ============== Response Models ==============

class AttendanceLogResponse(BaseModel):
    """Ответ с записью журнала посещений."""
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    event_type: EventType
    timestamp: datetime
    confidence: float
    trace_id: str

    class Config:
        from_attributes = True


class EmployeeStatusResponse(BaseModel):
    """Статус присутствия сотрудника."""
    employee_id: int
    employee_name: str
    status: PresenceStatus
    last_event: Optional[EventType] = None
    last_event_time: Optional[datetime] = None


class AttendanceStatsResponse(BaseModel):
    """Агрегированная статистика посещений."""
    employee_id: int
    employee_name: str
    total_days: int = Field(..., description="Всего дней с посещениями")
    total_hours: float = Field(..., description="Общее время в офисе (часы)")
    avg_arrival_time: Optional[str] = Field(None, description="Среднее время прихода")
    avg_departure_time: Optional[str] = Field(None, description="Среднее время ухода")


class OfficeStatusResponse(BaseModel):
    """Общий статус офиса."""
    present_count: int = Field(..., description="Сотрудников в офисе")
    total_employees: int = Field(..., description="Всего сотрудников")
    present_employees: list[EmployeeStatusResponse] = Field(default_factory=list)


# ============== Internal Models ==============

class AttendanceLogCreate(BaseModel):
    """Внутренняя модель для создания записи."""
    employee_id: int
    event_type: EventType
    confidence: float
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AttendanceLogInDB(AttendanceLogResponse):
    """Модель записи как она хранится в БД."""
    created_at: datetime
    updated_at: Optional[datetime] = None
