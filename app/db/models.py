"""
SQLAlchemy модели базы данных.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Text,
    LargeBinary,
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


class Employee(Base):
    """
    Модель сотрудника.
    """

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    department = Column(String(100), nullable=True)
    photo_path = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    embeddings = relationship(
        "Embedding",
        back_populates="employee",
        cascade="all, delete-orphan"
    )
    attendance_logs = relationship(
        "AttendanceLog",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.full_name})>"


class Embedding(Base):
    """
    Модель для хранения face embeddings (векторов лиц).
    """

    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Храним вектор как бинарные данные (для SQLite совместимости)
    # В PostgreSQL можно использовать ARRAY(Float)
    vector_blob = Column(LargeBinary, nullable=False)
    vector_dim = Column(Integer, nullable=False, default=512)
    model_version = Column(String(50), nullable=False, default="arcface")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    employee = relationship("Employee", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, employee_id={self.employee_id}, model={self.model_version})>"


class AttendanceLog(Base):
    """Журнал посещений."""

    __tablename__ = "attendance_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True
    )
    event_type = Column(SQLEnum(EventType), nullable=False, default=EventType.ENTRY)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    confidence = Column(Float, nullable=True)
    trace_id = Column(String(64), nullable=False)
    photo_path = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="unknown")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    employee = relationship("Employee", back_populates="attendance_logs")

    # Индексы для быстрого поиска
    __table_args__ = (
        Index("ix_attendance_log_employee_id", "employee_id"),
        Index("ix_attendance_log_timestamp", "timestamp"),
        Index("ix_attendance_log_employee_timestamp", "employee_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee_id={self.employee_id}, event={self.event_type}, time={self.timestamp})>"
