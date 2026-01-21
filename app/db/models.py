"""
SQLAlchemy модели базы данных.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class EventType(str, enum.Enum):
    """Тип события посещения."""
    ENTRY = "entry"
    EXIT = "exit"


class AttendanceLog(Base):
    """Журнал посещений."""

    __tablename__ = "attendance_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False, default=EventType.ENTRY)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    confidence = Column(Float, nullable=False)
    trace_id = Column(String(64), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship (будет работать когда появится модель Employee)
    # employee = relationship("Employee", back_populates="attendance_logs")

    # Индексы для быстрого поиска
    __table_args__ = (
        Index("ix_attendance_log_employee_id", "employee_id"),
        Index("ix_attendance_log_timestamp", "timestamp"),
        Index("ix_attendance_log_employee_timestamp", "employee_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee_id={self.employee_id}, event={self.event_type}, time={self.timestamp})>"


class Employee(Base):
    """
    Модель сотрудника (заглушка).

    TODO: Будет заменена на полную версию из модуля employees (Ольга).
    """

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)  # SQLite совместимость

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    # attendance_logs = relationship("AttendanceLog", back_populates="employee")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.full_name})>"
