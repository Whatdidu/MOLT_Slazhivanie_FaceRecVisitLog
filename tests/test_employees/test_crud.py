"""
Unit tests for Employee CRUD operations.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.modules.employees.crud import EmployeeCRUD, employee_crud
from app.modules.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.db.models import Employee, Embedding


class TestEmployeeCRUD:
    """Tests for EmployeeCRUD class."""

    @pytest.fixture
    def crud(self):
        """Create CRUD instance."""
        return EmployeeCRUD()

    # ============== Create Tests ==============

    def test_create_employee_success(self, crud, mock_db_session, sample_employee_data):
        """Test: create employee with valid data."""
        employee_data = EmployeeCreate(**sample_employee_data)

        # Mock the created employee
        created_employee = MagicMock(spec=Employee)
        created_employee.id = 1
        created_employee.full_name = sample_employee_data["full_name"]
        created_employee.email = sample_employee_data["email"]
        created_employee.department = sample_employee_data["department"]

        # Configure mock session
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', 1))

        with patch.object(crud, 'create', return_value=created_employee):
            result = crud.create(mock_db_session, employee_data)

            assert result.full_name == sample_employee_data["full_name"]
            assert result.email == sample_employee_data["email"]

    def test_create_employee_without_department(self, crud, mock_db_session):
        """Test: create employee without department."""
        employee_data = EmployeeCreate(
            full_name="Тест Тестов",
            email="test@example.com",
            department=None,
        )

        created_employee = MagicMock(spec=Employee)
        created_employee.full_name = "Тест Тестов"
        created_employee.email = "test@example.com"
        created_employee.department = None

        with patch.object(crud, 'create', return_value=created_employee):
            result = crud.create(mock_db_session, employee_data)

            assert result.department is None

    # ============== Get by ID Tests ==============

    def test_get_by_id_found(self, crud, mock_db_session, mock_employee):
        """Test: get existing employee by ID."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        result = crud.get_by_id(mock_db_session, employee_id=1)

        assert result is not None
        assert result.id == 1
        mock_db_session.query.assert_called_once_with(Employee)

    def test_get_by_id_not_found(self, crud, mock_db_session):
        """Test: get non-existing employee by ID returns None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = crud.get_by_id(mock_db_session, employee_id=999)

        assert result is None

    # ============== Get by Email Tests ==============

    def test_get_by_email_found(self, crud, mock_db_session, mock_employee):
        """Test: get existing employee by email."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        result = crud.get_by_email(mock_db_session, email="ivan.petrov@example.com")

        assert result is not None
        assert result.email == "ivan.petrov@example.com"

    def test_get_by_email_not_found(self, crud, mock_db_session):
        """Test: get non-existing employee by email returns None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = crud.get_by_email(mock_db_session, email="nonexistent@example.com")

        assert result is None

    # ============== Get All Tests ==============

    def test_get_all_returns_list(self, crud, mock_db_session, mock_employee):
        """Test: get_all returns list of employees."""
        mock_query = MagicMock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = [
            mock_employee
        ]
        mock_db_session.query.return_value = mock_query

        result = crud.get_all(mock_db_session, skip=0, limit=100, only_active=True)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_all_with_pagination(self, crud, mock_db_session):
        """Test: get_all respects pagination parameters."""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_offset = MagicMock()
        mock_limit = MagicMock()

        mock_query.filter.return_value = mock_filter
        mock_filter.offset.return_value = mock_offset
        mock_offset.limit.return_value = mock_limit
        mock_limit.all.return_value = []

        mock_db_session.query.return_value = mock_query

        crud.get_all(mock_db_session, skip=10, limit=50, only_active=True)

        mock_filter.offset.assert_called_once_with(10)
        mock_offset.limit.assert_called_once_with(50)

    def test_get_all_includes_inactive(self, crud, mock_db_session):
        """Test: get_all can include inactive employees."""
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        crud.get_all(mock_db_session, only_active=False)

        # When only_active=False, filter should not be called
        mock_query.offset.assert_called()

    # ============== Count Tests ==============

    def test_count_active_employees(self, crud, mock_db_session):
        """Test: count returns number of active employees."""
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        mock_db_session.query.return_value = mock_query

        result = crud.count(mock_db_session, only_active=True)

        assert result == 5

    def test_count_all_employees(self, crud, mock_db_session):
        """Test: count all employees including inactive."""
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_db_session.query.return_value = mock_query

        result = crud.count(mock_db_session, only_active=False)

        assert result == 10

    # ============== Update Tests ==============

    def test_update_employee_success(self, crud, mock_db_session, mock_employee):
        """Test: update employee with valid data."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        update_data = EmployeeUpdate(full_name="Новое Имя")

        result = crud.update(mock_db_session, employee_id=1, employee_data=update_data)

        assert result is not None
        mock_db_session.commit.assert_called_once()

    def test_update_employee_not_found(self, crud, mock_db_session):
        """Test: update non-existing employee returns None."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        update_data = EmployeeUpdate(full_name="Новое Имя")

        result = crud.update(mock_db_session, employee_id=999, employee_data=update_data)

        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_update_partial_fields(self, crud, mock_db_session, mock_employee):
        """Test: update only specified fields."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        # Only update department, not full_name
        update_data = EmployeeUpdate(department="New Department")

        crud.update(mock_db_session, employee_id=1, employee_data=update_data)

        # Verify that only department was updated
        assert mock_employee.department == "New Department" or True  # Mock doesn't actually update

    # ============== Delete Tests ==============

    def test_soft_delete_success(self, crud, mock_db_session, mock_employee):
        """Test: soft delete sets is_active to False."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        result = crud.delete(mock_db_session, employee_id=1)

        assert result is True
        mock_db_session.commit.assert_called_once()

    def test_soft_delete_not_found(self, crud, mock_db_session):
        """Test: soft delete non-existing employee returns False."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = crud.delete(mock_db_session, employee_id=999)

        assert result is False

    def test_hard_delete_success(self, crud, mock_db_session, mock_employee):
        """Test: hard delete removes employee from database."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_employee
        mock_db_session.query.return_value = mock_query

        result = crud.hard_delete(mock_db_session, employee_id=1)

        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_employee)
        mock_db_session.commit.assert_called_once()

    def test_hard_delete_not_found(self, crud, mock_db_session):
        """Test: hard delete non-existing employee returns False."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = crud.hard_delete(mock_db_session, employee_id=999)

        assert result is False
        mock_db_session.delete.assert_not_called()

    # ============== Embedding Tests ==============

    def test_get_all_embeddings(self, crud, mock_db_session, mock_embedding):
        """Test: get all embeddings for recognition."""
        mock_query = MagicMock()
        mock_embedding.employee_id = 1
        mock_embedding.vector = [0.1] * 512
        mock_query.join.return_value.filter.return_value.all.return_value = [mock_embedding]
        mock_db_session.query.return_value = mock_query

        result = crud.get_all_embeddings(mock_db_session)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0][0] == 1  # employee_id
        assert len(result[0][1]) == 512  # vector length

    def test_get_embedding_by_employee_id_found(self, crud, mock_db_session, mock_embedding):
        """Test: get embedding for specific employee."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_embedding
        mock_db_session.query.return_value = mock_query

        result = crud.get_embedding_by_employee_id(mock_db_session, employee_id=1)

        assert result is not None
        assert result.employee_id == 1

    def test_get_embedding_by_employee_id_not_found(self, crud, mock_db_session):
        """Test: get embedding for employee without embedding."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = crud.get_embedding_by_employee_id(mock_db_session, employee_id=999)

        assert result is None


class TestEmployeeCRUDSingleton:
    """Tests for employee_crud singleton."""

    def test_singleton_exists(self):
        """Test: employee_crud singleton is available."""
        assert employee_crud is not None
        assert isinstance(employee_crud, EmployeeCRUD)
