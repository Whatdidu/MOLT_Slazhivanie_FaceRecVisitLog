"""
Интеграция модуля Attendance с другими модулями.

Обработчики событий от:
- Recognition: после успешного распознавания лица
- Employees: при создании/удалении сотрудников
"""

import uuid
from typing import Optional
from datetime import datetime

from app.modules.attendance.service import get_attendance_service
from app.modules.attendance.models import AttendanceLogResponse, EventType


class AttendanceIntegration:
    """
    Класс интеграции для внешних модулей.

    Использование:
        from app.modules.attendance.integration import attendance_integration

        # После распознавания лица (из модуля Recognition)
        await attendance_integration.on_face_recognized(
            employee_id=123,
            confidence=0.85,
            trace_id="abc-123"
        )
    """

    def __init__(self):
        self._service = None

    @property
    def service(self):
        if self._service is None:
            self._service = get_attendance_service()
        return self._service

    # ============== Recognition Integration ==============

    async def on_face_recognized(
        self,
        employee_id: int,
        confidence: float,
        trace_id: Optional[str] = None,
        event_type: EventType = EventType.ENTRY,
    ) -> Optional[AttendanceLogResponse]:
        """
        Обработчик события распознавания лица.

        Вызывается модулем Recognition после успешного распознавания.

        Args:
            employee_id: ID распознанного сотрудника
            confidence: Уверенность распознавания (0.0-1.0)
            trace_id: Сквозной ID запроса (генерируется если не передан)
            event_type: Тип события (вход/выход)

        Returns:
            Запись журнала или None если сработал анти-спам
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        # Проверяем анти-спам
        can_log = await self.service.can_log_entry(employee_id)
        if not can_log:
            return None

        # Записываем событие
        if event_type == EventType.ENTRY:
            return await self.service.log_entry(
                employee_id=employee_id,
                confidence=confidence,
                trace_id=trace_id,
            )
        else:
            return await self.service.log_exit(
                employee_id=employee_id,
                trace_id=trace_id,
            )

    async def on_unknown_face(
        self,
        confidence: float,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Обработчик события неизвестного лица.

        Может использоваться для логирования попыток входа неизвестных людей.

        Args:
            confidence: Максимальная уверенность среди всех сравнений
            trace_id: Сквозной ID запроса
        """
        # TODO: Логирование неизвестных лиц в отдельную таблицу
        # Для MVP просто игнорируем
        pass

    async def on_low_confidence(
        self,
        employee_id: int,
        confidence: float,
        trace_id: Optional[str] = None,
    ) -> None:
        """
        Обработчик события низкой уверенности распознавания.

        Может использоваться для пометки сомнительных распознаваний.

        Args:
            employee_id: Предполагаемый ID сотрудника
            confidence: Уверенность распознавания
            trace_id: Сквозной ID запроса
        """
        # TODO: Логирование low_confidence событий
        # Для MVP просто игнорируем
        pass

    # ============== Employees Integration ==============

    async def on_employee_created(self, employee_id: int) -> None:
        """
        Обработчик создания нового сотрудника.

        Вызывается модулем Employees после создания сотрудника.

        Args:
            employee_id: ID нового сотрудника
        """
        # Для MVP ничего не делаем, но можно:
        # - Отправить уведомление
        # - Создать запись в аудит логе
        pass

    async def on_employee_deactivated(self, employee_id: int) -> None:
        """
        Обработчик деактивации сотрудника.

        Вызывается модулем Employees при деактивации сотрудника.

        Args:
            employee_id: ID деактивированного сотрудника
        """
        # Для MVP ничего не делаем, но можно:
        # - Пометить текущий статус как "ушёл"
        # - Создать запись в аудит логе
        pass


# Singleton instance для использования другими модулями
attendance_integration = AttendanceIntegration()


# ============== Удобные функции ==============

async def log_recognition_event(
    employee_id: int,
    confidence: float,
    trace_id: Optional[str] = None,
) -> Optional[AttendanceLogResponse]:
    """
    Быстрая функция для логирования события распознавания.

    Использование из модуля Recognition:
        from app.modules.attendance.integration import log_recognition_event

        result = await log_recognition_event(
            employee_id=person_id,
            confidence=match_confidence,
            trace_id=request_trace_id,
        )
    """
    return await attendance_integration.on_face_recognized(
        employee_id=employee_id,
        confidence=confidence,
        trace_id=trace_id,
    )
