"""
Pydantic schemas for Employee API.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# Base schema with common fields
class EmployeeBase(BaseModel):
    """Base schema for Employee with common fields."""

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the employee"
    )
    email: EmailStr = Field(
        ...,
        description="Unique email address"
    )
    department: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Department name"
    )


# Schema for creating a new employee
class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee."""

    pass  # Inherits all fields from EmployeeBase


# Schema for updating an employee
class EmployeeUpdate(BaseModel):
    """Schema for updating an employee (all fields optional)."""

    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Full name of the employee"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Unique email address"
    )
    department: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Department name"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the employee is active"
    )


# Schema for employee enrollment (with photo)
class EmployeeEnrollRequest(EmployeeBase):
    """Schema for employee enrollment request."""

    # Photo will be uploaded as multipart/form-data
    # This schema is for JSON body validation


# Schema for employee response
class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""

    id: int = Field(..., description="Employee ID")
    photo_path: Optional[str] = Field(
        default=None,
        description="Path to employee photo"
    )
    is_active: bool = Field(
        default=True,
        description="Whether the employee is active"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    has_embedding: Optional[bool] = Field(
        default=None,
        description="Whether the employee has a face embedding for recognition"
    )

    model_config = ConfigDict(from_attributes=True)


# Schema for employee list response
class EmployeeListResponse(BaseModel):
    """Schema for employee list response with pagination."""

    total: int = Field(..., description="Total number of employees")
    skip: int = Field(..., description="Number of skipped items")
    limit: int = Field(..., description="Maximum number of items")
    items: list[EmployeeResponse] = Field(..., description="List of employees")


# Schema for embedding response
class EmbeddingResponse(BaseModel):
    """Schema for embedding response."""

    id: int = Field(..., description="Embedding ID")
    employee_id: int = Field(..., description="Employee ID")
    model_version: str = Field(..., description="ML model version")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# Schema for enrollment response
class EmployeeEnrollResponse(BaseModel):
    """Schema for employee enrollment response."""

    employee: EmployeeResponse = Field(..., description="Created employee")
    embedding: EmbeddingResponse = Field(..., description="Created embedding")
    message: str = Field(
        default="Employee enrolled successfully",
        description="Success message"
    )
