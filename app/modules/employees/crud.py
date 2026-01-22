"""
CRUD operations for Employee model.
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.db.models import Employee, Embedding
from app.modules.employees.schemas import EmployeeCreate, EmployeeUpdate


class EmployeeCRUD:
    """CRUD operations for Employee model."""

    @staticmethod
    def create(db: Session, employee_data: EmployeeCreate) -> Employee:
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
        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def get_by_id(db: Session, employee_id: int) -> Optional[Employee]:
        """
        Get employee by ID.

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            Employee instance or None if not found
        """
        return db.query(Employee).filter(Employee.id == employee_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Employee]:
        """
        Get employee by email.

        Args:
            db: Database session
            email: Employee email

        Returns:
            Employee instance or None if not found
        """
        return db.query(Employee).filter(Employee.email == email).first()

    @staticmethod
    def get_all(
        db: Session,
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
        query = db.query(Employee)

        if only_active:
            query = query.filter(Employee.is_active == True)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def count(db: Session, only_active: bool = True) -> int:
        """
        Count total number of employees.

        Args:
            db: Database session
            only_active: Count only active employees

        Returns:
            Total number of employees
        """
        query = db.query(Employee)

        if only_active:
            query = query.filter(Employee.is_active == True)

        return query.count()

    @staticmethod
    def update(
        db: Session,
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
        employee = db.query(Employee).filter(Employee.id == employee_id).first()

        if not employee:
            return None

        # Update only provided fields
        update_data = employee_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee, field, value)

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def delete(db: Session, employee_id: int) -> bool:
        """
        Soft delete employee (set is_active=False).

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            True if deleted, False if not found
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()

        if not employee:
            return False

        employee.is_active = False
        db.commit()
        return True

    @staticmethod
    def hard_delete(db: Session, employee_id: int) -> bool:
        """
        Hard delete employee from database.

        Args:
            db: Database session
            employee_id: Employee ID

        Returns:
            True if deleted, False if not found
        """
        employee = db.query(Employee).filter(Employee.id == employee_id).first()

        if not employee:
            return False

        db.delete(employee)
        db.commit()
        return True

    @staticmethod
    def get_all_embeddings(db: Session) -> list[tuple[int, list[float]]]:
        """
        Get all employee embeddings for recognition.

        Returns:
            List of tuples (employee_id, vector)
        """
        embeddings = db.query(Embedding).join(Employee).filter(
            Employee.is_active == True
        ).all()

        return [(emb.employee_id, emb.vector) for emb in embeddings]

    @staticmethod
    def get_embedding_by_employee_id(
        db: Session,
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
        return db.query(Embedding).filter(
            Embedding.employee_id == employee_id
        ).first()


# Global instance
employee_crud = EmployeeCRUD()
