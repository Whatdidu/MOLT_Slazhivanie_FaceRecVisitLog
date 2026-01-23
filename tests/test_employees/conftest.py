"""
Pytest fixtures for Employee module tests.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.db.models import Employee, Embedding


@pytest.fixture
def sample_employee_data() -> dict:
    """Sample employee creation data."""
    return {
        "full_name": "Иван Петров",
        "email": "ivan.petrov@example.com",
        "department": "IT Department",
    }


@pytest.fixture
def sample_employee_update_data() -> dict:
    """Sample employee update data."""
    return {
        "full_name": "Иван Сидоров",
        "department": "HR Department",
    }


@pytest.fixture
def mock_employee() -> MagicMock:
    """Mock Employee model instance."""
    employee = MagicMock(spec=Employee)
    employee.id = 1
    employee.full_name = "Иван Петров"
    employee.email = "ivan.petrov@example.com"
    employee.department = "IT Department"
    employee.photo_path = None
    employee.is_active = True
    employee.created_at = datetime(2024, 1, 15, 10, 0, 0)
    employee.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return employee


@pytest.fixture
def mock_employee_with_photo() -> MagicMock:
    """Mock Employee model instance with photo."""
    employee = MagicMock(spec=Employee)
    employee.id = 1
    employee.full_name = "Мария Иванова"
    employee.email = "maria.ivanova@example.com"
    employee.department = "Sales"
    employee.photo_path = "employee_photos/maria_ivanova_20240115_100000_abc123.jpg"
    employee.is_active = True
    employee.created_at = datetime(2024, 1, 15, 10, 0, 0)
    employee.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return employee


@pytest.fixture
def mock_embedding() -> MagicMock:
    """Mock Embedding model instance."""
    embedding = MagicMock(spec=Embedding)
    embedding.id = 1
    embedding.employee_id = 1
    embedding.vector = [0.1] * 512  # 512-dimensional vector
    embedding.model_version = "arcface"
    embedding.created_at = datetime(2024, 1, 15, 10, 0, 0)
    embedding.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return embedding


@pytest.fixture
def mock_embedding_result():
    """Mock EmbeddingResult from recognition service."""
    from app.modules.recognition.models import EmbeddingResult
    return EmbeddingResult(
        embedding=[0.1] * 512,
        face_detected=True,
        face_quality=0.85,
        bbox=(100, 100, 200, 200),
    )


@pytest.fixture
def mock_embedding_result_no_face():
    """Mock EmbeddingResult with no face detected."""
    from app.modules.recognition.models import EmbeddingResult
    return EmbeddingResult(
        embedding=[],
        face_detected=False,
        face_quality=0.0,
        bbox=None,
    )


@pytest.fixture
def mock_embedding_result_low_quality():
    """Mock EmbeddingResult with low quality face."""
    from app.modules.recognition.models import EmbeddingResult
    return EmbeddingResult(
        embedding=[0.1] * 512,
        face_detected=True,
        face_quality=0.15,  # Below threshold
        bbox=(100, 100, 200, 200),
    )
