"""
Unit tests for Employee Service (Enrollment flow).
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.modules.employees.service import (
    EmployeeService,
    get_employee_service,
    EmailAlreadyExistsError,
    NoFaceDetectedError,
    LowQualityPhotoError,
)
from app.modules.employees.schemas import EmployeeCreate, EmployeeUpdate
from app.db.models import Employee, Embedding


class TestEmployeeService:
    """Tests for EmployeeService class."""

    @pytest.fixture
    def service(self):
        """Create service instance with mocked recognition."""
        service = EmployeeService()
        service._recognition_service = MagicMock()
        return service

    # ============== Enroll Employee Tests ==============

    @pytest.mark.asyncio
    async def test_enroll_employee_success(
        self,
        service,
        mock_db_session,
        sample_employee_data,
        mock_embedding_result,
        sample_photo_bytes,
    ):
        """Test: successful employee enrollment."""
        # Mock recognition service
        service._recognition_service.create_embedding = AsyncMock(
            return_value=mock_embedding_result
        )

        # Mock CRUD operations
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_email.return_value = None  # Email not exists

            mock_employee = MagicMock(spec=Employee)
            mock_employee.id = 1
            mock_employee.full_name = sample_employee_data["full_name"]
            mock_employee.email = sample_employee_data["email"]
            mock_crud.create.return_value = mock_employee

            # Mock photo saving
            with patch.object(service, '_save_photo', new_callable=AsyncMock) as mock_save:
                mock_save.return_value = "employee_photos/test.jpg"

                employee, embedding = await service.enroll_employee(
                    db=mock_db_session,
                    full_name=sample_employee_data["full_name"],
                    email=sample_employee_data["email"],
                    photo=sample_photo_bytes,
                    department=sample_employee_data["department"],
                )

                assert employee is not None
                assert employee.id == 1
                mock_crud.get_by_email.assert_called_once()
                mock_crud.create.assert_called_once()
                mock_db_session.add.assert_called()  # Embedding added
                mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_enroll_employee_email_exists(
        self,
        service,
        mock_db_session,
        sample_employee_data,
        mock_employee,
        sample_photo_bytes,
    ):
        """Test: enrollment fails if email already exists."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_email.return_value = mock_employee  # Email exists

            with pytest.raises(EmailAlreadyExistsError) as exc_info:
                await service.enroll_employee(
                    db=mock_db_session,
                    full_name=sample_employee_data["full_name"],
                    email=sample_employee_data["email"],
                    photo=sample_photo_bytes,
                )

            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_enroll_employee_no_face_detected(
        self,
        service,
        mock_db_session,
        sample_employee_data,
        mock_embedding_result_no_face,
        sample_photo_bytes,
    ):
        """Test: enrollment fails if no face detected in photo."""
        service._recognition_service.create_embedding = AsyncMock(
            return_value=mock_embedding_result_no_face
        )

        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_email.return_value = None

            with pytest.raises(NoFaceDetectedError) as exc_info:
                await service.enroll_employee(
                    db=mock_db_session,
                    full_name=sample_employee_data["full_name"],
                    email=sample_employee_data["email"],
                    photo=sample_photo_bytes,
                )

            assert "No face detected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_enroll_employee_low_quality_photo(
        self,
        service,
        mock_db_session,
        sample_employee_data,
        mock_embedding_result_low_quality,
        sample_photo_bytes,
    ):
        """Test: enrollment fails if photo quality is too low."""
        service._recognition_service.create_embedding = AsyncMock(
            return_value=mock_embedding_result_low_quality
        )

        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_email.return_value = None

            with pytest.raises(LowQualityPhotoError) as exc_info:
                await service.enroll_employee(
                    db=mock_db_session,
                    full_name=sample_employee_data["full_name"],
                    email=sample_employee_data["email"],
                    photo=sample_photo_bytes,
                )

            assert "quality" in str(exc_info.value).lower()

    # ============== Update Photo Tests ==============

    @pytest.mark.asyncio
    async def test_update_employee_photo_success(
        self,
        service,
        mock_db_session,
        mock_employee_with_photo,
        mock_embedding,
        mock_embedding_result,
        sample_photo_bytes,
    ):
        """Test: successful photo update."""
        service._recognition_service.create_embedding = AsyncMock(
            return_value=mock_embedding_result
        )

        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_id.return_value = mock_employee_with_photo
            mock_crud.get_embedding_by_employee_id.return_value = mock_embedding

            with patch.object(service, '_save_photo', new_callable=AsyncMock) as mock_save:
                mock_save.return_value = "employee_photos/new_photo.jpg"

                with patch.object(service, '_delete_photo', new_callable=AsyncMock) as mock_delete:
                    result = await service.update_employee_photo(
                        db=mock_db_session,
                        employee_id=1,
                        photo=sample_photo_bytes,
                    )

                    assert result is not None
                    mock_delete.assert_called_once()  # Old photo deleted
                    mock_save.assert_called_once()  # New photo saved

    @pytest.mark.asyncio
    async def test_update_employee_photo_not_found(
        self,
        service,
        mock_db_session,
        sample_photo_bytes,
    ):
        """Test: update photo fails for non-existing employee."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_id.return_value = None

            with pytest.raises(ValueError) as exc_info:
                await service.update_employee_photo(
                    db=mock_db_session,
                    employee_id=999,
                    photo=sample_photo_bytes,
                )

            assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_employee_photo_no_face(
        self,
        service,
        mock_db_session,
        mock_employee_with_photo,
        mock_embedding_result_no_face,
        sample_photo_bytes,
    ):
        """Test: update photo fails if no face in new photo."""
        service._recognition_service.create_embedding = AsyncMock(
            return_value=mock_embedding_result_no_face
        )

        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_id.return_value = mock_employee_with_photo

            with pytest.raises(NoFaceDetectedError):
                await service.update_employee_photo(
                    db=mock_db_session,
                    employee_id=1,
                    photo=sample_photo_bytes,
                )

    # ============== Photo Storage Tests ==============

    @pytest.mark.asyncio
    async def test_save_photo_creates_file(self, service, sample_photo_bytes):
        """Test: _save_photo creates file with correct path."""
        with patch('app.modules.employees.service.Path') as mock_path:
            mock_photos_dir = MagicMock()
            mock_path.return_value.__truediv__.return_value = mock_photos_dir
            mock_photos_dir.mkdir = MagicMock()

            mock_file_path = MagicMock()
            mock_photos_dir.__truediv__.return_value = mock_file_path
            mock_file_path.write_bytes = MagicMock()

            with patch('app.modules.employees.service.settings') as mock_settings:
                mock_settings.static_path = "app/static"

                result = await service._save_photo(sample_photo_bytes, "test@example.com")

                assert result is not None
                assert "employee_photos" in result

    @pytest.mark.asyncio
    async def test_delete_photo_removes_file(self, service):
        """Test: _delete_photo removes existing file."""
        with patch('app.modules.employees.service.Path') as mock_path:
            mock_file = MagicMock()
            mock_path.return_value.__truediv__.return_value = mock_file
            mock_file.exists.return_value = True
            mock_file.unlink = MagicMock()

            with patch('app.modules.employees.service.settings') as mock_settings:
                mock_settings.static_path = "app/static"

                await service._delete_photo("employee_photos/old_photo.jpg")

                mock_file.unlink.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_photo_skips_nonexistent(self, service):
        """Test: _delete_photo does nothing for non-existing file."""
        with patch('app.modules.employees.service.Path') as mock_path:
            mock_file = MagicMock()
            mock_path.return_value.__truediv__.return_value = mock_file
            mock_file.exists.return_value = False
            mock_file.unlink = MagicMock()

            with patch('app.modules.employees.service.settings') as mock_settings:
                mock_settings.static_path = "app/static"

                await service._delete_photo("employee_photos/nonexistent.jpg")

                mock_file.unlink.assert_not_called()

    # ============== Convenience Methods Tests ==============

    def test_get_employee_delegates_to_crud(self, service, mock_db_session, mock_employee):
        """Test: get_employee delegates to CRUD."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_id.return_value = mock_employee

            result = service.get_employee(mock_db_session, employee_id=1)

            assert result == mock_employee
            mock_crud.get_by_id.assert_called_once_with(mock_db_session, 1)

    def test_get_employee_by_email_delegates_to_crud(self, service, mock_db_session, mock_employee):
        """Test: get_employee_by_email delegates to CRUD."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_by_email.return_value = mock_employee

            result = service.get_employee_by_email(mock_db_session, email="test@example.com")

            assert result == mock_employee
            mock_crud.get_by_email.assert_called_once_with(mock_db_session, "test@example.com")

    def test_list_employees_delegates_to_crud(self, service, mock_db_session, mock_employee):
        """Test: list_employees delegates to CRUD."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.get_all.return_value = [mock_employee]

            result = service.list_employees(mock_db_session, skip=0, limit=100)

            assert result == [mock_employee]
            mock_crud.get_all.assert_called_once()

    def test_delete_employee_delegates_to_crud(self, service, mock_db_session):
        """Test: delete_employee delegates to CRUD."""
        with patch('app.modules.employees.service.employee_crud') as mock_crud:
            mock_crud.delete.return_value = True

            result = service.delete_employee(mock_db_session, employee_id=1)

            assert result is True
            mock_crud.delete.assert_called_once_with(mock_db_session, 1)


class TestEmployeeServiceSingleton:
    """Tests for get_employee_service singleton."""

    def test_singleton_returns_same_instance(self):
        """Test: get_employee_service returns singleton."""
        service1 = get_employee_service()
        service2 = get_employee_service()

        assert service1 is service2

    def test_singleton_is_employee_service(self):
        """Test: singleton is EmployeeService instance."""
        service = get_employee_service()

        assert isinstance(service, EmployeeService)


class TestEmployeeServiceExceptions:
    """Tests for custom exceptions."""

    def test_email_already_exists_error(self):
        """Test: EmailAlreadyExistsError message."""
        error = EmailAlreadyExistsError("test@example.com already exists")
        assert "already exists" in str(error)

    def test_no_face_detected_error(self):
        """Test: NoFaceDetectedError message."""
        error = NoFaceDetectedError("No face detected")
        assert "No face" in str(error)

    def test_low_quality_photo_error(self):
        """Test: LowQualityPhotoError message."""
        error = LowQualityPhotoError("Photo quality 0.10 is below threshold")
        assert "quality" in str(error).lower()
