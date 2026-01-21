"""
Integration-тесты для API модуля Attendance.
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI

from app.modules.attendance.router import router
from app.modules.attendance.models import (
    EventType,
    PresenceStatus,
    AttendanceLogResponse,
    EmployeeStatusResponse,
    OfficeStatusResponse,
)


# Создаём тестовое приложение
app = FastAPI()
app.include_router(router)


class TestAttendanceAPI:
    """Тесты для REST API."""

    @pytest.fixture
    def mock_service(self):
        """Мок сервиса."""
        with patch('app.modules.attendance.router.get_attendance_service') as mock:
            service = MagicMock()
            mock.return_value = service
            yield service

    @pytest.mark.asyncio
    async def test_log_attendance_entry(self, mock_service):
        """Тест: POST /log создаёт запись входа."""
        mock_service.can_log_entry = AsyncMock(return_value=True)
        mock_service.log_entry = AsyncMock(return_value=AttendanceLogResponse(
            id=1,
            employee_id=1,
            employee_name="Test User",
            event_type=EventType.ENTRY,
            timestamp=date.today(),
            confidence=0.85,
            trace_id="test-123",
        ))

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/attendance/log", json={
                "employee_id": 1,
                "event_type": "entry",
                "confidence": 0.85,
                "trace_id": "test-123",
            })

        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == 1
        assert data["event_type"] == "entry"

    @pytest.mark.asyncio
    async def test_log_attendance_rate_limited(self, mock_service):
        """Тест: POST /log возвращает 429 при анти-спам."""
        mock_service.can_log_entry = AsyncMock(return_value=False)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/attendance/log", json={
                "employee_id": 1,
                "event_type": "entry",
                "confidence": 0.85,
                "trace_id": "test-123",
            })

        assert response.status_code == 429
        assert "Too many requests" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_office_status(self, mock_service):
        """Тест: GET /status возвращает статус офиса."""
        mock_service.get_office_status = AsyncMock(return_value=OfficeStatusResponse(
            present_count=5,
            total_employees=20,
            present_employees=[],
        ))

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/status")

        assert response.status_code == 200
        data = response.json()
        assert data["present_count"] == 5
        assert data["total_employees"] == 20

    @pytest.mark.asyncio
    async def test_get_employee_status(self, mock_service):
        """Тест: GET /status/{id} возвращает статус сотрудника."""
        mock_service.get_employee_status = AsyncMock(return_value=EmployeeStatusResponse(
            employee_id=1,
            employee_name="Test User",
            status=PresenceStatus.IN_OFFICE,
            last_event=EventType.ENTRY,
            last_event_time=None,
        ))

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/status/1")

        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == 1
        assert data["status"] == "in_office"

    @pytest.mark.asyncio
    async def test_get_attendance_history(self, mock_service):
        """Тест: GET /history возвращает историю."""
        mock_service.get_attendance_history = AsyncMock(return_value=[])

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/history", params={
                "start_date": str(date.today() - timedelta(days=7)),
                "end_date": str(date.today()),
            })

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_history_invalid_dates(self, mock_service):
        """Тест: GET /history с неверными датами возвращает 400."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/history", params={
                "start_date": str(date.today()),
                "end_date": str(date.today() - timedelta(days=7)),  # end < start
            })

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Тест: GET /health возвращает статус OK."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "attendance"


class TestExportAPI:
    """Тесты для API экспорта."""

    @pytest.fixture
    def mock_service(self):
        with patch('app.modules.attendance.router.get_attendance_service') as mock:
            service = MagicMock()
            mock.return_value = service
            yield service

    @pytest.mark.asyncio
    async def test_export_json(self, mock_service):
        """Тест: GET /export/json возвращает JSON файл."""
        mock_service.get_attendance_history = AsyncMock(return_value=[])

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/export/json", params={
                "start_date": str(date.today() - timedelta(days=7)),
                "end_date": str(date.today()),
            })

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]
        assert "attachment" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_export_excel(self, mock_service):
        """Тест: GET /export/excel возвращает Excel файл."""
        mock_service.get_attendance_history = AsyncMock(return_value=[])

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/attendance/export/excel", params={
                "start_date": str(date.today() - timedelta(days=7)),
                "end_date": str(date.today()),
            })

        assert response.status_code == 200
        assert "spreadsheet" in response.headers["content-type"]


class TestIntegration:
    """Тесты интеграции с другими модулями."""

    @pytest.mark.asyncio
    async def test_recognition_integration(self):
        """Тест: интеграция с модулем Recognition."""
        from app.modules.attendance.integration import attendance_integration

        with patch('app.modules.attendance.integration.get_attendance_service') as mock:
            service = MagicMock()
            service.can_log_entry = AsyncMock(return_value=True)
            service.log_entry = AsyncMock(return_value=AttendanceLogResponse(
                id=1,
                employee_id=1,
                employee_name="Test",
                event_type=EventType.ENTRY,
                timestamp=date.today(),
                confidence=0.9,
                trace_id="test",
            ))
            mock.return_value = service

            # Сбрасываем кэшированный сервис
            attendance_integration._service = None

            result = await attendance_integration.on_face_recognized(
                employee_id=1,
                confidence=0.9,
                trace_id="test-recognition",
            )

            assert result is not None
            assert result.employee_id == 1

    @pytest.mark.asyncio
    async def test_recognition_integration_rate_limited(self):
        """Тест: интеграция возвращает None при анти-спам."""
        from app.modules.attendance.integration import attendance_integration

        with patch('app.modules.attendance.integration.get_attendance_service') as mock:
            service = MagicMock()
            service.can_log_entry = AsyncMock(return_value=False)
            mock.return_value = service

            attendance_integration._service = None

            result = await attendance_integration.on_face_recognized(
                employee_id=1,
                confidence=0.9,
            )

            assert result is None
