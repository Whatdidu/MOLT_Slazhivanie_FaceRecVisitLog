"""
Employees module - CRUD operations and API for employee management.
"""
from app.modules.employees.router import router
from app.modules.employees.crud import employee_crud
from app.modules.employees.service import get_employee_service, EmployeeService
from app.modules.employees.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeEnrollRequest,
    EmployeeEnrollResponse,
)

__all__ = [
    "router",
    "employee_crud",
    "get_employee_service",
    "EmployeeService",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeListResponse",
    "EmployeeEnrollRequest",
    "EmployeeEnrollResponse",
]
