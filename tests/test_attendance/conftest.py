"""
Pytest fixtures для тестов модуля Attendance.
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создаём event loop для async тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_employee_data():
    """Тестовые данные сотрудника."""
    return {
        "id": 1,
        "first_name": "Иван",
        "last_name": "Петров",
        "department": "IT",
        "is_active": True,
    }


@pytest.fixture
def sample_log_data():
    """Тестовые данные записи журнала."""
    return {
        "employee_id": 1,
        "event_type": "entry",
        "confidence": 0.85,
        "trace_id": "test-trace-123",
    }
