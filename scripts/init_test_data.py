"""
Script to initialize test data in the database.
Run after applying migrations.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Employee
from app.core.logger import logger


def create_test_employees(db: Session) -> None:
    """Create test employees."""

    test_employees = [
        {
            "full_name": "Иван Иванов",
            "email": "ivan.ivanov@sputnik.com",
            "department": "Engineering"
        },
        {
            "full_name": "Мария Петрова",
            "email": "maria.petrova@sputnik.com",
            "department": "HR"
        },
        {
            "full_name": "Алексей Сидоров",
            "email": "alexey.sidorov@sputnik.com",
            "department": "Sales"
        },
        {
            "full_name": "Ольга Кузнецова",
            "email": "olga.kuznetsova@sputnik.com",
            "department": "Engineering"
        },
        {
            "full_name": "Дмитрий Смирнов",
            "email": "dmitry.smirnov@sputnik.com",
            "department": "Management"
        }
    ]

    for emp_data in test_employees:
        # Check if employee already exists
        existing = db.query(Employee).filter(
            Employee.email == emp_data["email"]
        ).first()

        if existing:
            logger.info(f"Employee {emp_data['full_name']} already exists, skipping")
            continue

        employee = Employee(**emp_data)
        db.add(employee)
        logger.info(f"Created employee: {emp_data['full_name']}")

    db.commit()
    logger.info("Test data initialization completed")


def main():
    """Main function."""
    logger.info("Starting test data initialization...")

    db = SessionLocal()
    try:
        create_test_employees(db)
    except Exception as e:
        logger.error(f"Failed to initialize test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
