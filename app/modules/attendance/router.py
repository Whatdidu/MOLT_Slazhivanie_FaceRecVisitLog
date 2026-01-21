"""
FastAPI роутер для модуля Attendance.

Endpoints:
- POST /log - Записать событие
- GET /status - Список сотрудников со статусом
- GET /status/{employee_id} - Статус конкретного сотрудника
- GET /history - История посещений
- GET /export/json - Экспорт в JSON
- GET /export/excel - Экспорт в Excel
- GET /stats - Агрегированная статистика
"""

from datetime import date, timedelta
from typing import Optional
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse, Response

from app.modules.attendance.models import (
    AttendanceLogRequest,
    AttendanceLogResponse,
    EmployeeStatusResponse,
    OfficeStatusResponse,
    AttendanceStatsResponse,
    EventType,
)
from app.modules.attendance.service import get_attendance_service
from app.modules.attendance.export import AttendanceExporter, export_to_json, export_to_excel


router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


# ============== Логирование событий ==============

@router.post("/log", response_model=AttendanceLogResponse)
async def log_attendance(request: AttendanceLogRequest):
    """
    Записать событие посещения (вход/выход).

    - **employee_id**: ID сотрудника
    - **event_type**: Тип события (entry/exit)
    - **confidence**: Уверенность распознавания (0.0-1.0)
    - **trace_id**: Сквозной ID для логирования
    """
    service = get_attendance_service()

    # Проверка анти-спам для входов
    if request.event_type == EventType.ENTRY:
        can_log = await service.can_log_entry(request.employee_id)
        if not can_log:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before logging another entry.",
            )

    # Создание записи
    if request.event_type == EventType.ENTRY:
        log = await service.log_entry(
            employee_id=request.employee_id,
            confidence=request.confidence,
            trace_id=request.trace_id,
        )
    else:
        log = await service.log_exit(
            employee_id=request.employee_id,
            trace_id=request.trace_id,
        )

    return log


# ============== Статусы присутствия ==============

@router.get("/status", response_model=OfficeStatusResponse)
async def get_office_status():
    """
    Получить общий статус офиса.

    Возвращает количество сотрудников в офисе и их список.
    """
    service = get_attendance_service()
    return await service.get_office_status()


@router.get("/status/{employee_id}", response_model=EmployeeStatusResponse)
async def get_employee_status(employee_id: int):
    """
    Получить статус присутствия конкретного сотрудника.

    - **employee_id**: ID сотрудника
    """
    service = get_attendance_service()
    return await service.get_employee_status(employee_id)


# ============== История посещений ==============

@router.get("/history", response_model=list[AttendanceLogResponse])
async def get_attendance_history(
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=7),
        description="Начало периода (по умолчанию: 7 дней назад)",
    ),
    end_date: date = Query(
        default_factory=date.today,
        description="Конец периода (по умолчанию: сегодня)",
    ),
    employee_id: Optional[int] = Query(
        None,
        description="Фильтр по ID сотрудника",
    ),
):
    """
    Получить историю посещений за период.

    - **start_date**: Начало периода
    - **end_date**: Конец периода
    - **employee_id**: Фильтр по сотруднику (опционально)
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    service = get_attendance_service()
    return await service.get_attendance_history(
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
    )


# ============== Экспорт данных ==============

@router.get("/export/json")
async def export_json_endpoint(
    start_date: date = Query(..., description="Начало периода"),
    end_date: date = Query(..., description="Конец периода"),
    employee_id: Optional[int] = Query(None, description="Фильтр по сотруднику"),
    department: Optional[str] = Query(None, description="Фильтр по отделу"),
):
    """
    Экспорт истории посещений в JSON.

    Возвращает файл для скачивания.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    service = get_attendance_service()
    history = await service.get_attendance_history(
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
    )

    # Экспорт через модуль
    json_bytes = export_to_json(history)
    filename = f"attendance_{start_date}_{end_date}.json"

    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


@router.get("/export/excel")
async def export_excel_endpoint(
    start_date: date = Query(..., description="Начало периода"),
    end_date: date = Query(..., description="Конец периода"),
    employee_id: Optional[int] = Query(None, description="Фильтр по сотруднику"),
    department: Optional[str] = Query(None, description="Фильтр по отделу"),
):
    """
    Экспорт истории посещений в Excel.

    Возвращает .xlsx файл для скачивания.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    service = get_attendance_service()
    history = await service.get_attendance_history(
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
    )

    # Экспорт через модуль
    excel_bytes = export_to_excel(history, start_date=start_date, end_date=end_date)
    filename = f"attendance_{start_date}_{end_date}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


# ============== Статистика ==============

@router.get("/stats/{employee_id}", response_model=AttendanceStatsResponse)
async def get_attendance_stats(
    employee_id: int,
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Начало периода",
    ),
    end_date: date = Query(
        default_factory=date.today,
        description="Конец периода",
    ),
):
    """
    Получить агрегированную статистику посещений сотрудника.

    - **employee_id**: ID сотрудника
    - **start_date**: Начало периода
    - **end_date**: Конец периода
    """
    service = get_attendance_service()
    return await service.get_attendance_stats(
        start_date=start_date,
        end_date=end_date,
        employee_id=employee_id,
    )


# ============== Сводная статистика ==============

@router.get("/stats", response_model=list[AttendanceStatsResponse])
async def get_all_stats(
    start_date: date = Query(
        default_factory=lambda: date.today() - timedelta(days=30),
        description="Начало периода",
    ),
    end_date: date = Query(
        default_factory=date.today,
        description="Конец периода",
    ),
):
    """
    Получить статистику посещений по всем сотрудникам.

    - **start_date**: Начало периода
    - **end_date**: Конец периода
    """
    service = get_attendance_service()

    # Получаем всех сотрудников из истории
    history = await service.get_attendance_history(start_date, end_date)
    employee_ids = set(log.employee_id for log in history)

    # Собираем статистику по каждому
    stats_list = []
    for emp_id in employee_ids:
        stats = await service.get_attendance_stats(start_date, end_date, emp_id)
        stats_list.append(stats)

    # Сортируем по часам (больше часов - выше)
    stats_list.sort(key=lambda x: x.total_hours, reverse=True)

    return stats_list


@router.get("/export/stats/excel")
async def export_stats_excel(
    start_date: date = Query(..., description="Начало периода"),
    end_date: date = Query(..., description="Конец периода"),
):
    """
    Экспорт сводной статистики в Excel.

    Возвращает .xlsx файл со статистикой по всем сотрудникам.
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    service = get_attendance_service()

    # Получаем статистику
    history = await service.get_attendance_history(start_date, end_date)
    employee_ids = set(log.employee_id for log in history)

    stats_list = []
    for emp_id in employee_ids:
        stats = await service.get_attendance_stats(start_date, end_date, emp_id)
        stats_list.append(stats)

    stats_list.sort(key=lambda x: x.total_hours, reverse=True)

    # Экспорт
    excel_bytes = AttendanceExporter.stats_to_excel(
        stats_list,
        start_date=start_date,
        end_date=end_date,
    )
    filename = f"attendance_stats_{start_date}_{end_date}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


# ============== Health Check ==============

@router.get("/health")
async def health_check():
    """Проверка работоспособности модуля."""
    return {"status": "ok", "module": "attendance"}
