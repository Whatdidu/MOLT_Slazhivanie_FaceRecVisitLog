"""
Base class for SQLAlchemy models with common fields.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.db.session import Base


class TimestampMixin:
    """Mixin that adds timestamp fields to models."""

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Record creation timestamp (UTC)"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Record last update timestamp (UTC)"
    )


class BaseModel(Base, TimestampMixin):
    """
    Base model class with auto-incrementing ID and timestamps.
    All models should inherit from this class.
    """

    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="Primary key"
    )

    @declared_attr
    def __tablename__(cls):
        """Auto-generate table name from class name."""
        return cls.__name__.lower()

    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
