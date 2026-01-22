"""
Сервис учёта посещаемости.

Содержит бизнес-логику:
- Логирование входов/выходов
- Анти-спам фильтрация
- Получение статусов присутствия
- Формирование отчётов
"""

from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session, AttendanceLog, Employee
from app.db.models import EventType as DBEventType
from app.modules.attendance.models import (
    AttendanceLogResponse,
    EmployeeStatusResponse,
    OfficeStatusResponse,
    AttendanceStatsResponse,
    EventType,
    PresenceStatus,
)


# Конфигурация
COOLDOWN_SECONDS = 300  # 5 минут между записями
WORK_DAY_START = 6  # 06:00
WORK_DAY_END = 23  # 23:00


class AttendanceService:
    """Сервис управления посещаемостью."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session

    # ============== Логирование событий ==============

    async def log_entry(
        self,
        employee_id: int,
        confidence: float,
        trace_id: str,
    ) -> AttendanceLogResponse:
        """
        Записать вход сотрудника.

        Args:
            employee_id: ID сотрудника
            confidence: Уверенность распознавания (0.0-1.0)
            trace_id: Сквозной ID для логирования

        Returns:
            Созданная запись журнала
        """
        return await self._create_log(
            employee_id=employee_id,
            event_type=EventType.ENTRY,
            confidence=confidence,
            trace_id=trace_id,
        )

    async def log_exit(
        self,
        employee_id: int,
        trace_id: str,
    ) -> AttendanceLogResponse:
        """
        Записать выход сотрудника.

        Args:
            employee_id: ID сотрудника
            trace_id: Сквозной ID для логирования

        Returns:
            Созданная запись журнала
        """
        return await self._create_log(
            employee_id=employee_id,
            event_type=EventType.EXIT,
            confidence=1.0,  # Выход обычно явный
            trace_id=trace_id,
        )

    async def _create_log(
        self,
        employee_id: int,
        event_type: EventType,
        confidence: float,
        trace_id: str,
    ) -> AttendanceLogResponse:
        """Внутренний метод создания записи в БД."""
        async with get_session() as session:
            # Получаем имя сотрудника
            employee_name = await self._get_employee_name(session, employee_id)

            # Создаём запись
            db_event_type = DBEventType.ENTRY if event_type == EventType.ENTRY else DBEventType.EXIT
            log = AttendanceLog(
                employee_id=employee_id,
                event_type=db_event_type,
                confidence=confidence,
                trace_id=trace_id,
                timestamp=datetime.now(),
            )

            session.add(log)
            await session.flush()
            await session.refresh(log)

            return AttendanceLogResponse(
                id=log.id,
                employee_id=log.employee_id,
                employee_name=employee_name,
                event_type=event_type,
                timestamp=log.timestamp,
                confidence=log.confidence,
                trace_id=log.trace_id,
            )

    async def _get_employee_name(self, session: AsyncSession, employee_id: int) -> str:
        """Получить имя сотрудника из БД."""
        result = await session.execute(
            select(Employee).where(Employee.id == employee_id)
        )
        employee = result.scalar_one_or_none()
        if employee:
            return employee.full_name
        return f"Employee #{employee_id}"

    # ============== Анти-спам фильтрация ==============

    async def can_log_entry(
        self,
        employee_id: int,
        cooldown_seconds: int = COOLDOWN_SECONDS,
    ) -> bool:
        """
        Проверить, можно ли записать новый вход (анти-спам).

        Args:
            employee_id: ID сотрудника
            cooldown_seconds: Минимальный интервал между записями

        Returns:
            True если можно записать, False если слишком рано
        """
        async with get_session() as session:
            # Получаем последнюю запись сотрудника
            result = await session.execute(
                select(AttendanceLog)
                .where(AttendanceLog.employee_id == employee_id)
                .order_by(desc(AttendanceLog.timestamp))
                .limit(1)
            )
            last_log = result.scalar_one_or_none()

            if last_log is None:
                return True

            elapsed = datetime.now() - last_log.timestamp
            return elapsed.total_seconds() >= cooldown_seconds

    async def _get_last_log(self, session: AsyncSession, employee_id: int) -> Optional[AttendanceLog]:
        """Получить последнюю запись сотрудника из БД."""
        result = await session.execute(
            select(AttendanceLog)
            .where(AttendanceLog.employee_id == employee_id)
            .order_by(desc(AttendanceLog.timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ============== Статусы присутствия ==============

    async def get_employee_status(self, employee_id: int) -> EmployeeStatusResponse:
        """
        Получить текущий статус присутствия сотрудника.

        Args:
            employee_id: ID сотрудника

        Returns:
            Статус присутствия
        """
        async with get_session() as session:
            # Получаем сотрудника
            employee_name = await self._get_employee_name(session, employee_id)

            # Получаем последнюю запись
            last_log = await self._get_last_log(session, employee_id)

            if last_log is None:
                return EmployeeStatusResponse(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    status=PresenceStatus.UNKNOWN,
                )

            # Определяем статус по последнему событию
            if last_log.event_type == DBEventType.ENTRY:
                status = PresenceStatus.IN_OFFICE
                event_type = EventType.ENTRY
            else:
                status = PresenceStatus.LEFT
                event_type = EventType.EXIT

            return EmployeeStatusResponse(
                employee_id=employee_id,
                employee_name=employee_name,
                status=status,
                last_event=event_type,
                last_event_time=last_log.timestamp,
            )

    async def get_present_employees(self) -> list[EmployeeStatusResponse]:
        """
        Получить список сотрудников, находящихся в офисе.

        Returns:
            Список сотрудников со статусом IN_OFFICE
        """
        async with get_session() as session:
            # Подзапрос: последняя запись для каждого сотрудника
            subquery = (
                select(
                    AttendanceLog.employee_id,
                    func.max(AttendanceLog.timestamp).label("max_timestamp")
                )
                .group_by(AttendanceLog.employee_id)
                .subquery()
            )

            # Получаем последние записи с типом ENTRY
            result = await session.execute(
                select(AttendanceLog)
                .join(
                    subquery,
                    and_(
                        AttendanceLog.employee_id == subquery.c.employee_id,
                        AttendanceLog.timestamp == subquery.c.max_timestamp,
                    )
                )
                .where(AttendanceLog.event_type == DBEventType.ENTRY)
            )

            logs = result.scalars().all()

            present = []
            for log in logs:
                employee_name = await self._get_employee_name(session, log.employee_id)
                present.append(EmployeeStatusResponse(
                    employee_id=log.employee_id,
                    employee_name=employee_name,
                    status=PresenceStatus.IN_OFFICE,
                    last_event=EventType.ENTRY,
                    last_event_time=log.timestamp,
                ))

            return present

    async def get_office_status(self) -> OfficeStatusResponse:
        """
        Получить общий статус офиса.

        Returns:
            Статус офиса с количеством присутствующих
        """
        async with get_session() as session:
            present = await self.get_present_employees()

            # Получаем общее количество активных сотрудников
            result = await session.execute(
                select(func.count(Employee.id)).where(Employee.is_active == 1)
            )
            total_employees = result.scalar() or 0

            return OfficeStatusResponse(
                present_count=len(present),
                total_employees=total_employees,
                present_employees=present,
            )

    # ============== История и отчёты ==============

    async def get_attendance_history(
        self,
        start_date: date,
        end_date: date,
        employee_id: Optional[int] = None,
    ) -> list[AttendanceLogResponse]:
        """
        Получить историю посещений за период.

        Args:
            start_date: Начало периода
            end_date: Конец периода
            employee_id: Фильтр по сотруднику (опционально)

        Returns:
            Список записей журнала
        """
        async with get_session() as session:
            # Преобразуем даты в datetime
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            # Строим запрос
            query = (
                select(AttendanceLog)
                .where(
                    and_(
                        AttendanceLog.timestamp >= start_datetime,
                        AttendanceLog.timestamp <= end_datetime,
                    )
                )
                .order_by(desc(AttendanceLog.timestamp))
            )

            # Фильтр по сотруднику
            if employee_id is not None:
                query = query.where(AttendanceLog.employee_id == employee_id)

            result = await session.execute(query)
            logs = result.scalars().all()

            # Преобразуем в response модели
            responses = []
            for log in logs:
                employee_name = await self._get_employee_name(session, log.employee_id)
                event_type = EventType.ENTRY if log.event_type == DBEventType.ENTRY else EventType.EXIT

                responses.append(AttendanceLogResponse(
                    id=log.id,
                    employee_id=log.employee_id,
                    employee_name=employee_name,
                    event_type=event_type,
                    timestamp=log.timestamp,
                    confidence=log.confidence,
                    trace_id=log.trace_id,
                ))

            return responses

    async def get_attendance_stats(
        self,
        start_date: date,
        end_date: date,
        employee_id: int,
    ) -> AttendanceStatsResponse:
        """
        Получить агрегированную статистику посещений.

        Args:
            start_date: Начало периода
            end_date: Конец периода
            employee_id: ID сотрудника

        Returns:
            Статистика посещений
        """
        history = await self.get_attendance_history(start_date, end_date, employee_id)

        if not history:
            async with get_session() as session:
                employee_name = await self._get_employee_name(session, employee_id)
            return AttendanceStatsResponse(
                employee_id=employee_id,
                employee_name=employee_name,
                total_days=0,
                total_hours=0.0,
            )

        # Считаем уникальные дни
        unique_days = set(log.timestamp.date() for log in history)

        # Считаем часы работы (разница между первым entry и последним exit за день)
        total_hours = 0.0
        days_with_data = {}

        for log in history:
            day = log.timestamp.date()
            if day not in days_with_data:
                days_with_data[day] = {"entries": [], "exits": []}

            if log.event_type == EventType.ENTRY:
                days_with_data[day]["entries"].append(log.timestamp)
            else:
                days_with_data[day]["exits"].append(log.timestamp)

        # Вычисляем часы для каждого дня
        for day, events in days_with_data.items():
            if events["entries"] and events["exits"]:
                first_entry = min(events["entries"])
                last_exit = max(events["exits"])
                if last_exit > first_entry:
                    hours = (last_exit - first_entry).total_seconds() / 3600
                    total_hours += hours

        # Среднее время прихода
        all_entries = []
        all_exits = []
        for log in history:
            if log.event_type == EventType.ENTRY:
                all_entries.append(log.timestamp.time())
            else:
                all_exits.append(log.timestamp.time())

        avg_arrival = None
        avg_departure = None

        if all_entries:
            avg_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in all_entries) / len(all_entries)
            hours = int(avg_seconds // 3600)
            minutes = int((avg_seconds % 3600) // 60)
            avg_arrival = f"{hours:02d}:{minutes:02d}"

        if all_exits:
            avg_seconds = sum(t.hour * 3600 + t.minute * 60 + t.second for t in all_exits) / len(all_exits)
            hours = int(avg_seconds // 3600)
            minutes = int((avg_seconds % 3600) // 60)
            avg_departure = f"{hours:02d}:{minutes:02d}"

        return AttendanceStatsResponse(
            employee_id=employee_id,
            employee_name=history[0].employee_name if history else f"Employee #{employee_id}",
            total_days=len(unique_days),
            total_hours=round(total_hours, 2),
            avg_arrival_time=avg_arrival,
            avg_departure_time=avg_departure,
        )


# ============== Singleton ==============

_attendance_service: Optional[AttendanceService] = None


def get_attendance_service() -> AttendanceService:
    """Получить singleton экземпляр сервиса."""
    global _attendance_service
    if _attendance_service is None:
        _attendance_service = AttendanceService()
    return _attendance_service
