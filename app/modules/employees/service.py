"""
Employee service for enrollment and management operations.
Integrates with Recognition module for face embedding creation.
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Employee, Embedding
from app.modules.employees.crud import employee_crud
from app.modules.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.modules.recognition.service import get_recognition_service


class EmployeeServiceError(Exception):
    """Base exception for employee service errors."""
    pass


class EmailAlreadyExistsError(EmployeeServiceError):
    """Raised when email already exists."""
    pass


class NoFaceDetectedError(EmployeeServiceError):
    """Raised when no face detected in photo."""
    pass


class LowQualityPhotoError(EmployeeServiceError):
    """Raised when photo quality is too low."""
    pass


class EmployeeService:
    """
    Service for employee enrollment and management.
    Orchestrates CRUD operations and face recognition integration.
    """

    # Minimum face quality threshold for enrollment
    MIN_FACE_QUALITY = 0.3

    def __init__(self):
        self._recognition_service = get_recognition_service()

    async def enroll_employee(
        self,
        db: AsyncSession,
        full_name: str,
        email: str,
        photo: bytes,
        department: Optional[str] = None,
    ) -> tuple[Employee, Embedding]:
        """
        Enroll a new employee with photo.

        Process:
        1. Check if email already exists
        2. Create face embedding from photo
        3. Save photo to temporary storage
        4. Create employee record
        5. Create embedding record

        Args:
            db: Database session
            full_name: Employee full name
            email: Employee email (unique)
            photo: Photo bytes (JPEG/PNG)
            department: Optional department name

        Returns:
            Tuple of (Employee, Embedding) instances

        Raises:
            EmailAlreadyExistsError: If email already exists
            NoFaceDetectedError: If no face detected in photo
            LowQualityPhotoError: If photo quality is too low
        """
        # Check email uniqueness
        existing = await employee_crud.get_by_email(db, email)
        if existing:
            raise EmailAlreadyExistsError(f"Employee with email {email} already exists")

        # Create embedding from photo
        embedding_result = await self._recognition_service.create_embedding(photo)

        if not embedding_result.face_detected:
            raise NoFaceDetectedError("No face detected in the provided photo")

        if embedding_result.face_quality < self.MIN_FACE_QUALITY:
            raise LowQualityPhotoError(
                f"Photo quality ({embedding_result.face_quality:.2f}) is below "
                f"minimum threshold ({self.MIN_FACE_QUALITY})"
            )

        # Save photo to temporary storage
        photo_path = await self._save_photo(photo, email)

        # Create employee record
        employee_data = EmployeeCreate(
            full_name=full_name,
            email=email,
            department=department,
        )
        employee = await employee_crud.create(db, employee_data)

        # Update photo path
        employee.photo_path = photo_path
        await db.commit()
        await db.refresh(employee)

        # Create embedding record
        embedding = Embedding(
            employee_id=employee.id,
            vector=embedding_result.embedding,
            model_version="arcface",
        )
        db.add(embedding)
        await db.commit()
        await db.refresh(embedding)

        return employee, embedding

    async def update_employee_photo(
        self,
        db: AsyncSession,
        employee_id: int,
        photo: bytes,
    ) -> Embedding:
        """
        Update employee photo and create new embedding.

        Args:
            db: Database session
            employee_id: Employee ID
            photo: New photo bytes

        Returns:
            New Embedding instance

        Raises:
            ValueError: If employee not found
            NoFaceDetectedError: If no face detected
            LowQualityPhotoError: If quality too low
        """
        employee = await employee_crud.get_by_id(db, employee_id)
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} not found")

        # Create new embedding
        embedding_result = await self._recognition_service.create_embedding(photo)

        if not embedding_result.face_detected:
            raise NoFaceDetectedError("No face detected in the provided photo")

        if embedding_result.face_quality < self.MIN_FACE_QUALITY:
            raise LowQualityPhotoError(
                f"Photo quality ({embedding_result.face_quality:.2f}) is below "
                f"minimum threshold ({self.MIN_FACE_QUALITY})"
            )

        # Delete old photo if exists
        if employee.photo_path:
            await self._delete_photo(employee.photo_path)

        # Save new photo
        photo_path = await self._save_photo(photo, employee.email)
        employee.photo_path = photo_path

        # Delete old embedding
        old_embedding = await employee_crud.get_embedding_by_employee_id(db, employee_id)
        if old_embedding:
            await db.delete(old_embedding)

        # Create new embedding
        embedding = Embedding(
            employee_id=employee.id,
            vector=embedding_result.embedding,
            model_version="arcface",
        )
        db.add(embedding)
        await db.commit()
        await db.refresh(embedding)

        return embedding

    async def _save_photo(self, photo: bytes, email: str) -> str:
        """
        Save photo to temporary storage.

        Args:
            photo: Photo bytes
            email: Employee email (for filename)

        Returns:
            Relative path to saved photo
        """
        # Create photos directory
        photos_dir = Path(settings.static_path) / "employee_photos"
        photos_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_email = email.replace("@", "_at_").replace(".", "_")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{safe_email}_{timestamp}_{unique_id}.jpg"

        # Save photo
        photo_path = photos_dir / filename
        photo_path.write_bytes(photo)

        # Return relative path
        return str(Path("employee_photos") / filename)

    async def _delete_photo(self, photo_path: str) -> None:
        """
        Delete photo from storage.

        Args:
            photo_path: Relative path to photo
        """
        full_path = Path(settings.static_path) / photo_path
        if full_path.exists():
            full_path.unlink()

    # Convenience wrappers for CRUD operations

    async def get_employee(self, db: AsyncSession, employee_id: int) -> Optional[Employee]:
        """Get employee by ID."""
        return await employee_crud.get_by_id(db, employee_id)

    async def get_employee_by_email(self, db: AsyncSession, email: str) -> Optional[Employee]:
        """Get employee by email."""
        return await employee_crud.get_by_email(db, email)

    async def list_employees(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True,
    ) -> list[Employee]:
        """Get list of employees."""
        return await employee_crud.get_all(db, skip=skip, limit=limit, only_active=only_active)

    async def update_employee(
        self,
        db: AsyncSession,
        employee_id: int,
        data: EmployeeUpdate,
    ) -> Optional[Employee]:
        """Update employee data."""
        return await employee_crud.update(db, employee_id, data)

    async def delete_employee(self, db: AsyncSession, employee_id: int) -> bool:
        """Soft delete employee."""
        return await employee_crud.delete(db, employee_id)

    async def get_all_embeddings(self, db: AsyncSession) -> list[tuple[int, list[float]]]:
        """Get all embeddings for recognition."""
        return await employee_crud.get_all_embeddings(db)


# Singleton instance
_employee_service: EmployeeService | None = None


def get_employee_service() -> EmployeeService:
    """Get singleton instance of EmployeeService."""
    global _employee_service
    if _employee_service is None:
        _employee_service = EmployeeService()
    return _employee_service
