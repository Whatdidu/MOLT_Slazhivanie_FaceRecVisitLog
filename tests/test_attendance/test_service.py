"""
Unit-тесты для AttendanceService.
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.attendance.service import AttendanceService, COOLDOWN_SECONDS
from app.modules.attendance.models import (
    EventType,
    PresenceStatus,
    AttendanceLogResponse,
    EmployeeStatusResponse,
)


class TestAttendanceService:
    """Тесты для AttendanceService."""

    @pytest.fixture
    def service(self):
        """Создание экземпляра сервиса."""
        return AttendanceService()

    # ============== Тесты log_entry / log_exit ==============

    @pytest.mark.asyncio
    async def test_log_entry_creates_record(self, service):
        """Тест: log_entry создаёт запись с правильными данными."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            # Мокаем сессию БД
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            # Мокаем запрос сотрудника
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_ctx.execute = AsyncMock(return_value=mock_result)
            mock_ctx.add = MagicMock()
            mock_ctx.flush = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            result = await service.log_entry(
                employee_id=1,
                confidence=0.85,
                trace_id="test-trace-123",
            )

            assert result.employee_id == 1
            assert result.confidence == 0.85
            assert result.trace_id == "test-trace-123"
            assert result.event_type == EventType.ENTRY

    @pytest.mark.asyncio
    async def test_log_exit_creates_record(self, service):
        """Тест: log_exit создаёт запись с confidence=1.0."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_ctx.execute = AsyncMock(return_value=mock_result)
            mock_ctx.add = MagicMock()
            mock_ctx.flush = AsyncMock()
            mock_ctx.refresh = AsyncMock()

            result = await service.log_exit(
                employee_id=1,
                trace_id="test-trace-456",
            )

            assert result.employee_id == 1
            assert result.confidence == 1.0
            assert result.event_type == EventType.EXIT

    # ============== Тесты анти-спам ==============

    @pytest.mark.asyncio
    async def test_can_log_entry_first_time(self, service):
        """Тест: первый вход разрешён."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            # Нет предыдущих записей
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_ctx.execute = AsyncMock(return_value=mock_result)

            result = await service.can_log_entry(employee_id=1)
            assert result is True

    @pytest.mark.asyncio
    async def test_can_log_entry_within_cooldown(self, service):
        """Тест: вход в течение cooldown запрещён."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            # Есть недавняя запись
            mock_log = MagicMock()
            mock_log.timestamp = datetime.now() - timedelta(seconds=60)  # 1 минута назад
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_ctx.execute = AsyncMock(return_value=mock_result)

            result = await service.can_log_entry(employee_id=1)
            assert result is False

    @pytest.mark.asyncio
    async def test_can_log_entry_after_cooldown(self, service):
        """Тест: вход после cooldown разрешён."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            # Старая запись
            mock_log = MagicMock()
            mock_log.timestamp = datetime.now() - timedelta(seconds=COOLDOWN_SECONDS + 60)
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_log
            mock_ctx.execute = AsyncMock(return_value=mock_result)

            result = await service.can_log_entry(employee_id=1)
            assert result is True

    # ============== Тесты статусов ==============

    @pytest.mark.asyncio
    async def test_get_employee_status_unknown(self, service):
        """Тест: статус UNKNOWN если нет записей."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_ctx.execute = AsyncMock(return_value=mock_result)

            result = await service.get_employee_status(employee_id=1)

            assert result.employee_id == 1
            assert result.status == PresenceStatus.UNKNOWN

    # ============== Тесты истории ==============

    @pytest.mark.asyncio
    async def test_get_attendance_history_filters_by_date(self, service):
        """Тест: история фильтруется по дате."""
        with patch('app.modules.attendance.service.get_session') as mock_session:
            mock_ctx = AsyncMock()
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_session.return_value.__aexit__ = AsyncMock()

            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_ctx.execute = AsyncMock(return_value=mock_result)

            result = await service.get_attendance_history(
                start_date=date.today() - timedelta(days=7),
                end_date=date.today(),
            )

            assert isinstance(result, list)
            # Проверяем что execute был вызван
            mock_ctx.execute.assert_called()


class TestAttendanceStats:
    """Тесты для статистики посещений."""

    @pytest.fixture
    def service(self):
        return AttendanceService()

    @pytest.mark.asyncio
    async def test_get_stats_empty_history(self, service):
        """Тест: статистика при пустой истории."""
        with patch.object(service, 'get_attendance_history', return_value=[]):
            with patch('app.modules.attendance.service.get_session') as mock_session:
                mock_ctx = AsyncMock()
                mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_ctx)
                mock_session.return_value.__aexit__ = AsyncMock()

                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_ctx.execute = AsyncMock(return_value=mock_result)

                result = await service.get_attendance_stats(
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                    employee_id=1,
                )

                assert result.employee_id == 1
                assert result.total_days == 0
                assert result.total_hours == 0.0

    @pytest.mark.asyncio
    async def test_get_stats_calculates_hours(self, service):
        """Тест: статистика правильно считает часы."""
        # Создаём тестовые записи
        test_logs = [
            AttendanceLogResponse(
                id=1,
                employee_id=1,
                employee_name="Test",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 15, 9, 0, 0),
                confidence=0.9,
                trace_id="t1",
            ),
            AttendanceLogResponse(
                id=2,
                employee_id=1,
                employee_name="Test",
                event_type=EventType.EXIT,
                timestamp=datetime(2024, 1, 15, 18, 0, 0),
                confidence=1.0,
                trace_id="t2",
            ),
        ]

        with patch.object(service, 'get_attendance_history', return_value=test_logs):
            result = await service.get_attendance_stats(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                employee_id=1,
            )

            assert result.total_days == 1
            assert result.total_hours == 9.0  # 9:00 - 18:00 = 9 часов
