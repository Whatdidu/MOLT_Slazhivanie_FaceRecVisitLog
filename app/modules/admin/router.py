"""
FastAPI роутер для веб-админки.

Routes:
- GET /admin/ - Dashboard
- GET /admin/present - Кто в офисе
- GET /admin/attendance - Журнал посещений
- GET /admin/employees - Список сотрудников
- GET /admin/employees/new - Форма добавления
- POST /admin/employees/new - Создание сотрудника
- GET /admin/reports - Отчёты
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Query, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, func

from app.db import get_session, Employee
from app.modules.attendance.service import get_attendance_service
from app.modules.attendance.models import EventType


router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


# ============== Dashboard ==============

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница админки."""
    service = get_attendance_service()

    # Получаем данные
    office_status = await service.get_office_status()
    today = date.today()
    today_logs = await service.get_attendance_history(today, today)

    # Считаем входы сегодня
    today_entries = sum(1 for log in today_logs if log.event_type == EventType.ENTRY)

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "present_count": office_status.present_count,
        "total_employees": office_status.total_employees,
        "present_employees": office_status.present_employees,
        "today_entries": today_entries,
        "current_date": today.strftime("%d.%m"),
        "recent_logs": today_logs[:10],
    })


# ============== Кто в офисе ==============

@router.get("/present", response_class=HTMLResponse)
async def present(request: Request):
    """Страница присутствующих сотрудников."""
    service = get_attendance_service()
    employees = await service.get_present_employees()

    return templates.TemplateResponse("admin/present.html", {
        "request": request,
        "active_page": "present",
        "employees": employees,
        "present_count": len(employees),
    })


# ============== Журнал посещений ==============

@router.get("/attendance", response_class=HTMLResponse)
async def attendance(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[int] = None,
):
    """Страница журнала посещений."""
    service = get_attendance_service()

    # Значения по умолчанию
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()

    # Получаем логи
    logs = await service.get_attendance_history(start_date, end_date, employee_id)

    # Получаем список сотрудников для фильтра
    async with get_session() as session:
        result = await session.execute(select(Employee).where(Employee.is_active == 1))
        employees_list = result.scalars().all()

    return templates.TemplateResponse("admin/attendance.html", {
        "request": request,
        "active_page": "attendance",
        "logs": logs,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "employee_id": employee_id,
        "employees_list": employees_list,
    })


# ============== Сотрудники ==============

@router.get("/employees", response_class=HTMLResponse)
async def employees(request: Request):
    """Страница списка сотрудников."""
    async with get_session() as session:
        result = await session.execute(
            select(Employee).order_by(Employee.last_name, Employee.first_name)
        )
        employees_list = result.scalars().all()

    return templates.TemplateResponse("admin/employees.html", {
        "request": request,
        "active_page": "employees",
        "employees": employees_list,
    })


@router.get("/employees/new", response_class=HTMLResponse)
async def new_employee_form(request: Request):
    """Форма создания нового сотрудника."""
    return templates.TemplateResponse("admin/employee_form.html", {
        "request": request,
        "active_page": "employees",
        "employee": None,
    })


@router.post("/employees/new", response_class=HTMLResponse)
async def create_employee(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    department: str = Form(None),
    photo: UploadFile = File(...),
):
    """Создание нового сотрудника."""
    error = None
    success = None

    try:
        async with get_session() as session:
            # Создаём сотрудника
            employee = Employee(
                first_name=first_name,
                last_name=last_name,
                department=department,
                is_active=1,
            )
            session.add(employee)
            await session.flush()

            # TODO: Обработка фото и создание embedding через модуль Recognition
            # photo_content = await photo.read()
            # embedding = await recognition_service.create_embedding(photo_content)

            await session.commit()
            success = f"Сотрудник {first_name} {last_name} успешно создан"

            return RedirectResponse(url="/admin/employees", status_code=303)

    except Exception as e:
        error = str(e)

    return templates.TemplateResponse("admin/employee_form.html", {
        "request": request,
        "active_page": "employees",
        "employee": None,
        "error": error,
        "success": success,
    })


@router.get("/employees/{employee_id}", response_class=HTMLResponse)
async def view_employee(request: Request, employee_id: int):
    """Просмотр карточки сотрудника."""
    async with get_session() as session:
        result = await session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()

    if not employee:
        return RedirectResponse(url="/admin/employees", status_code=303)

    # Получаем статистику сотрудника
    service = get_attendance_service()
    stats = await service.get_attendance_stats(
        start_date=date.today() - timedelta(days=30),
        end_date=date.today(),
        employee_id=employee_id,
    )

    return templates.TemplateResponse("admin/employee_form.html", {
        "request": request,
        "active_page": "employees",
        "employee": employee,
        "stats": stats,
    })


# ============== Отчёты ==============

@router.get("/reports", response_class=HTMLResponse)
async def reports(
    request: Request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Страница отчётов."""
    service = get_attendance_service()

    # Значения по умолчанию - последний месяц
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()

    # Получаем историю и статистику
    history = await service.get_attendance_history(start_date, end_date)

    # Собираем статистику по сотрудникам
    employee_ids = set(log.employee_id for log in history)
    stats = []
    for emp_id in employee_ids:
        s = await service.get_attendance_stats(start_date, end_date, emp_id)
        stats.append(s)
    stats.sort(key=lambda x: x.total_hours, reverse=True)

    # Общие метрики
    total_entries = sum(1 for log in history if log.event_type == EventType.ENTRY)
    unique_employees = len(employee_ids)
    avg_confidence = 0
    if history:
        avg_confidence = int(sum(log.confidence for log in history) / len(history) * 100)

    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "active_page": "reports",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "stats": stats,
        "total_entries": total_entries,
        "unique_employees": unique_employees,
        "avg_confidence": avg_confidence,
    })
