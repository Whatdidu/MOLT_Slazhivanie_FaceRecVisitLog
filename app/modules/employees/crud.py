"""
CRUD operations for Employee model (async version).
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists
from typing import Optional

from app.db.models import Employee, Embedding
from app.modules.employees.schemas import EmployeeCreate, EmployeeUpdate


class EmployeeCRUD:
    """CRUD operations for Employee model (async)."""

    @staticmethod
    async def create(db: AsyncSession, employee_data: EmployeeCreate) -> Employee:
        """
        Create a new employee.

        Args:
            db: Database session
            employee_data: Employee creation data

        Returns:
            Created employee instance

        Raises:
            IntegrityError: If email already exists
        """
        employee = Employee(
            full_name=employee_data.full_name,
            email=employee_data.email,
            department=employee_data.department,
        )
        db.add(employee)
        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def get_by_id(db: AsyncSession, employee_id: int) -> Optional[Employee]:
        """
        Get employee by ID.

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            Employee instance or None if not found
        """
        result = await db.execute(
            select(Employee).filter(Employee.id == employee_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Employee]:
        """
        Get employee by email.

        Args:
            db: Database session
            email: Employee email

        Returns:
            Employee instance or None if not found
        """
        result = await db.execute(
            select(Employee).filter(Employee.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True
    ) -> list[Employee]:
        """
        Get list of employees with pagination.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            only_active: Filter only active employees

        Returns:
            List of employees
        """
        query = select(Employee)

        if only_active:
            query = query.filter(Employee.is_active == True)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_with_embedding_status(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        only_active: bool = True
    ) -> list[tuple[Employee, bool]]:
        """
        Get list of employees with embedding status.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            only_active: Filter only active employees

        Returns:
            List of tuples (employee, has_embedding)
        """
        # Subquery to check if embedding exists
        embedding_exists = (
            select(Embedding.id)
            .where(Embedding.employee_id == Employee.id)
            .correlate(Employee)
            .exists()
        )

        query = select(Employee, embedding_exists.label("has_embedding"))

        if only_active:
            query = query.filter(Employee.is_active == True)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)

        return [(row[0], row[1]) for row in result.all()]

    @staticmethod
    async def count(db: AsyncSession, only_active: bool = True) -> int:
        """
        Count total number of employees.

        Args:
            db: Database session
            only_active: Count only active employees

        Returns:
            Total number of employees
        """
        query = select(func.count(Employee.id))

        if only_active:
            query = query.filter(Employee.is_active == True)

        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def update(
        db: AsyncSession,
        employee_id: int,
        employee_data: EmployeeUpdate
    ) -> Optional[Employee]:
        """
        Update employee data.

        Args:
            db: Database session
            employee_id: Employee ID
            employee_data: Employee update data

        Returns:
            Updated employee instance or None if not found
        """
        result = await db.execute(
            select(Employee).filter(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            return None

        # Update only provided fields
        update_data = employee_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        await db.commit()
        await db.refresh(employee)
        return employee

    @staticmethod
    async def delete(db: AsyncSession, employee_id: int) -> bool:
        """
        Soft delete employee (set is_active=False).

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Employee).filter(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            return False

        employee.is_active = False
        await db.commit()
        return True

    @staticmethod
    async def hard_delete(db: AsyncSession, employee_id: int) -> bool:
        """
        Hard delete employee from database.

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(Employee).filter(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

        if not employee:
            return False

        await db.delete(employee)
        await db.commit()
        return True

    @staticmethod
    async def get_all_embeddings(db: AsyncSession) -> list[tuple[int, list[float]]]:
        """
        Get all employee embeddings for recognition.

        Returns:
            List of tuples (employee_id, vector)
        """
        result = await db.execute(
            select(Embedding).join(Employee).filter(
                Employee.is_active == True
            )
        )
        embeddings = result.scalars().all()

        return [(emb.employee_id, emb.vector) for emb in embeddings]

    @staticmethod
    async def get_embedding_by_employee_id(
        db: AsyncSession,
        employee_id: int
    ) -> Optional[Embedding]:
        """
        Get embedding for specific employee.

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            Embedding instance or None if not found
        """
        result = await db.execute(
            select(Embedding).filter(Embedding.employee_id == employee_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_employees_with_embeddings(
        db: AsyncSession,
        only_active: bool = True
    ) -> list[tuple[Employee, Embedding]]:
        """
        Get all employees with their embeddings.

        Args:
            db: Database session
            only_active: Filter only active employees

        Returns:
            List of tuples (employee, embedding)
        """
        query = (
            select(Employee, Embedding)
            .join(Embedding, Employee.id == Embedding.employee_id)
        )

        if only_active:
            query = query.filter(Employee.is_active == True)

        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]


# Global instance
employee_crud = EmployeeCRUD()
