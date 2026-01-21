"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel


class Employee(BaseModel):
    """
    Employee model for storing employee information.

    Fields:
        id: Primary key (inherited from BaseModel)
        full_name: Full name of the employee
        email: Unique email address
        department: Department name (optional)
        photo_path: Path to employee photo (optional, deleted after embedding creation)
        is_active: Whether the employee is active (soft delete)
        created_at: Record creation timestamp (inherited from BaseModel)
        updated_at: Record last update timestamp (inherited from BaseModel)
    """

    __tablename__ = "employees"

    full_name = Column(
        String(255),
        nullable=False,
        comment="Full name of the employee"
    )
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address"
    )
    department = Column(
        String(100),
        nullable=True,
        comment="Department name"
    )
    photo_path = Column(
        String(500),
        nullable=True,
        comment="Path to employee photo (temporary)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the employee is active"
    )

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
        return f"<Employee(id={self.id}, name='{self.full_name}', email='{self.email}')>"


class Embedding(BaseModel):
    """
    Embedding model for storing face embeddings (vectors).

    Fields:
        id: Primary key (inherited from BaseModel)
        employee_id: Foreign key to Employee
        vector: Face embedding vector (array of floats)
        model_version: Version of the ML model used
        created_at: Record creation timestamp (inherited from BaseModel)
        updated_at: Record last update timestamp (inherited from BaseModel)
    """

    __tablename__ = "embeddings"

    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to Employee"
    )
    vector = Column(
        ARRAY(Float),
        nullable=False,
        comment="Face embedding vector"
    )
    model_version = Column(
        String(50),
        nullable=False,
        default="arcface",
        comment="ML model version used"
    )

    # Relationships
    employee = relationship("Employee", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, employee_id={self.employee_id}, model='{self.model_version}')>"


class AttendanceLog(BaseModel):
    """
    Attendance log model for tracking employee visits.

    Fields:
        id: Primary key (inherited from BaseModel)
        employee_id: Foreign key to Employee (nullable for unknown faces)
        timestamp: Event timestamp
        event_type: Type of event (entry/exit)
        confidence: Recognition confidence score (0-1)
        trace_id: Unique trace ID for request tracking
        photo_path: Path to snapshot photo (TTL 7 days)
        status: Recognition status (match/unknown/low_confidence/no_face/error)
        created_at: Record creation timestamp (inherited from BaseModel)
        updated_at: Record last update timestamp (inherited from BaseModel)
    """

    __tablename__ = "attendance_log"

    employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key to Employee (null for unknown faces)"
    )
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Event timestamp (UTC)"
    )
    event_type = Column(
        String(20),
        nullable=False,
        default="entry",
        comment="Event type (entry/exit)"
    )
    confidence = Column(
        Float,
        nullable=True,
        comment="Recognition confidence score (0-1)"
    )
    trace_id = Column(
        String(36),
        nullable=False,
        index=True,
        comment="Unique trace ID for request tracking (UUID)"
    )
    photo_path = Column(
        String(500),
        nullable=True,
        comment="Path to snapshot photo (TTL 7 days)"
    )
    status = Column(
        String(20),
        nullable=False,
        default="unknown",
        comment="Recognition status (match/unknown/low_confidence/no_face/error)"
    )

    # Relationships
    employee = relationship("Employee", back_populates="attendance_logs")

    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee_id={self.employee_id}, status='{self.status}', trace_id='{self.trace_id}')>"
