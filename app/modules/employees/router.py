"""
FastAPI router for Employee API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.db.session import get_db
from app.modules.employees.crud import employee_crud
from app.modules.employees.schemas import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
    EmployeeEnrollResponse,
    EmbeddingResponse,
)
from app.modules.employees.service import (
    get_employee_service,
    EmailAlreadyExistsError,
    NoFaceDetectedError,
    LowQualityPhotoError,
)

router = APIRouter(
    prefix="/api/v1/employees",
    tags=["employees"]
)


@router.post(
    "/enroll",
    response_model=EmployeeEnrollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll a new employee with photo"
)
async def enroll_employee(
    full_name: str = Form(..., description="Full name of the employee"),
    email: str = Form(..., description="Unique email address"),
    department: Optional[str] = Form(None, description="Department name"),
    photo: UploadFile = File(..., description="Employee photo (JPEG/PNG)"),
    db: Session = Depends(get_db)
):
    """
    Enroll a new employee with face photo.

    This endpoint:
    1. Validates the photo contains a detectable face
    2. Creates face embedding for recognition
    3. Saves the photo to storage
    4. Creates employee and embedding records

    - **full_name**: Full name of the employee
    - **email**: Unique email address
    - **department**: Department name (optional)
    - **photo**: Face photo file (JPEG/PNG, must contain one clear face)
    """
    # Validate file type
    if photo.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are supported."
        )

    # Read photo bytes
    photo_bytes = await photo.read()

    # Validate file size (max 10MB)
    if len(photo_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB."
        )

    service = get_employee_service()

    try:
        employee, embedding = await service.enroll_employee(
            db=db,
            full_name=full_name,
            email=email,
            photo=photo_bytes,
            department=department,
        )

        return EmployeeEnrollResponse(
            employee=EmployeeResponse.model_validate(employee),
            embedding=EmbeddingResponse.model_validate(embedding),
            message="Employee enrolled successfully",
        )

    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NoFaceDetectedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face detected in the provided photo. Please upload a clear photo with a visible face."
        )
    except LowQualityPhotoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll employee: {str(e)}"
        )


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new employee"
)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new employee with the following information:

    - **full_name**: Full name of the employee
    - **email**: Unique email address
    - **department**: Department name (optional)
    """
    # Check if email already exists
    existing = employee_crud.get_by_email(db, employee_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee with email {employee_data.email} already exists"
        )

    try:
        employee = employee_crud.create(db, employee_data)
        return employee
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create employee. Email might already exist."
        )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get employee by ID"
)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """
    Get employee information by ID.
    """
    employee = employee_crud.get_by_id(db, employee_id)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )

    return employee


@router.get(
    "/",
    response_model=EmployeeListResponse,
    summary="Get list of employees"
)
def list_employees(
    skip: int = 0,
    limit: int = 100,
    only_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get list of employees with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100, max: 500)
    - **only_active**: Filter only active employees (default: true)
    """
    # Limit max value
    limit = min(limit, 500)

    employees = employee_crud.get_all(db, skip=skip, limit=limit, only_active=only_active)
    total = employee_crud.count(db, only_active=only_active)

    return EmployeeListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=employees
    )


@router.put(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee"
)
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update employee information.

    Only provided fields will be updated.
    """
    employee = employee_crud.update(db, employee_id, employee_data)

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )

    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete employee"
)
def delete_employee(
    employee_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete employee.

    - **hard_delete**: If true, permanently delete from database. Otherwise, soft delete (set is_active=False)
    """
    if hard_delete:
        success = employee_crud.hard_delete(db, employee_id)
    else:
        success = employee_crud.delete(db, employee_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with ID {employee_id} not found"
        )

    return None


@router.get(
    "/embeddings/all",
    summary="Get all employee embeddings"
)
def get_all_embeddings(db: Session = Depends(get_db)):
    """
    Get all employee embeddings for recognition.

    Returns list of tuples (employee_id, vector).
    This endpoint is used by the recognition module.
    """
    embeddings = employee_crud.get_all_embeddings(db)

    return {
        "total": len(embeddings),
        "embeddings": [
            {"employee_id": emp_id, "vector": vector}
            for emp_id, vector in embeddings
        ]
    }
