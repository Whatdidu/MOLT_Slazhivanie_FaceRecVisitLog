"""
Unit tests for Storage Manager.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path

from app.core.storage import (
    StorageManager,
    get_storage_manager,
    cleanup_expired_photos,
)


class TestStorageManager:
    """Tests for StorageManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create StorageManager with temp directory."""
        return StorageManager(base_path=str(tmp_path), default_ttl_days=7)

    # ============== Initialization Tests ==============

    def test_init_with_defaults(self):
        """Test: initialization with default values."""
        manager = StorageManager()
        assert manager.default_ttl_days == 7  # From settings

    def test_init_with_custom_values(self, tmp_path):
        """Test: initialization with custom values."""
        manager = StorageManager(base_path=str(tmp_path), default_ttl_days=14)
        assert str(manager.base_path) == str(tmp_path)
        assert manager.default_ttl_days == 14

    def test_initialize_directories_creates_folders(self, manager, tmp_path):
        """Test: initialize_directories creates required folders."""
        manager.initialize_directories()

        debug_photos = tmp_path / "debug_photos"
        employee_photos = tmp_path / "employee_photos"

        assert debug_photos.exists()
        assert employee_photos.exists()

    # ============== Debug Photos Path Tests ==============

    def test_get_debug_photos_path_default_date(self, manager, tmp_path):
        """Test: get_debug_photos_path returns path for today."""
        manager.initialize_directories()
        path = manager.get_debug_photos_path()

        assert path.exists()
        assert "debug_photos" in str(path)
        assert datetime.utcnow().strftime("%Y-%m-%d") in str(path)

    def test_get_debug_photos_path_specific_date(self, manager, tmp_path):
        """Test: get_debug_photos_path returns path for specific date."""
        manager.initialize_directories()
        specific_date = datetime(2024, 6, 15)
        path = manager.get_debug_photos_path(date=specific_date)

        assert path.exists()
        assert "2024-06-15" in str(path)

    # ============== Save Debug Photo Tests ==============

    def test_save_debug_photo_creates_file(self, manager, tmp_path, sample_photo_bytes):
        """Test: save_debug_photo creates file with correct name."""
        manager.initialize_directories()

        result = manager.save_debug_photo(
            photo_bytes=sample_photo_bytes,
            trace_id="test-trace-123",
        )

        assert "debug_photos" in result
        assert "test-trace-123" in result
        assert result.endswith(".jpg")

        # Check file actually exists
        full_path = tmp_path / result
        assert full_path.exists()
        assert full_path.read_bytes() == sample_photo_bytes

    def test_save_debug_photo_with_timestamp(self, manager, tmp_path, sample_photo_bytes):
        """Test: save_debug_photo organizes by date."""
        manager.initialize_directories()
        specific_date = datetime(2024, 3, 20, 14, 30, 45)

        result = manager.save_debug_photo(
            photo_bytes=sample_photo_bytes,
            trace_id="trace-456",
            timestamp=specific_date,
        )

        assert "2024-03-20" in result
        assert "143045" in result  # HHMMSS format

    # ============== Cleanup Tests ==============

    def test_cleanup_removes_old_files(self, manager, tmp_path, sample_photo_bytes):
        """Test: cleanup removes files older than TTL."""
        manager.initialize_directories()
        manager.default_ttl_days = 7

        # Create old file
        old_date = datetime.utcnow() - timedelta(days=10)
        old_dir = manager.get_debug_photos_path(date=old_date)
        old_file = old_dir / "old_file.jpg"
        old_file.write_bytes(sample_photo_bytes)

        # Set file modification time to old date
        import os
        old_timestamp = old_date.timestamp()
        os.utime(old_file, (old_timestamp, old_timestamp))

        # Create recent file
        recent_dir = manager.get_debug_photos_path()
        recent_file = recent_dir / "recent_file.jpg"
        recent_file.write_bytes(sample_photo_bytes)

        # Run cleanup
        files_deleted, bytes_freed = manager.cleanup_expired_files()

        assert files_deleted >= 1
        assert bytes_freed > 0
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_dry_run_does_not_delete(self, manager, tmp_path, sample_photo_bytes):
        """Test: cleanup with dry_run=True doesn't delete files."""
        manager.initialize_directories()

        # Create old file
        old_date = datetime.utcnow() - timedelta(days=10)
        old_dir = manager.get_debug_photos_path(date=old_date)
        old_file = old_dir / "old_file.jpg"
        old_file.write_bytes(sample_photo_bytes)

        import os
        old_timestamp = old_date.timestamp()
        os.utime(old_file, (old_timestamp, old_timestamp))

        # Run cleanup in dry run mode
        files_deleted, bytes_freed = manager.cleanup_expired_files(dry_run=True)

        assert files_deleted >= 1
        assert old_file.exists()  # File should still exist

    def test_cleanup_preserves_gitkeep(self, manager, tmp_path):
        """Test: cleanup preserves .gitkeep files."""
        manager.initialize_directories()

        # Create .gitkeep
        debug_dir = tmp_path / "debug_photos"
        gitkeep = debug_dir / ".gitkeep"
        gitkeep.touch()

        # Run cleanup
        manager.cleanup_expired_files()

        assert gitkeep.exists()

    def test_cleanup_empty_directory_returns_zero(self, manager, tmp_path):
        """Test: cleanup on empty directory returns zeros."""
        manager.initialize_directories()

        files_deleted, bytes_freed = manager.cleanup_expired_files()

        assert files_deleted == 0
        assert bytes_freed == 0

    # ============== Storage Stats Tests ==============

    def test_get_storage_stats_empty(self, manager, tmp_path):
        """Test: get_storage_stats for empty storage."""
        manager.initialize_directories()

        stats = manager.get_storage_stats()

        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0
        assert "debug_photos" in stats["directories"]
        assert "employee_photos" in stats["directories"]

    def test_get_storage_stats_with_files(self, manager, tmp_path, sample_photo_bytes):
        """Test: get_storage_stats counts files correctly."""
        manager.initialize_directories()

        # Add some files
        debug_dir = tmp_path / "debug_photos" / "2024-01-15"
        debug_dir.mkdir(parents=True)
        (debug_dir / "photo1.jpg").write_bytes(sample_photo_bytes)
        (debug_dir / "photo2.jpg").write_bytes(sample_photo_bytes)

        stats = manager.get_storage_stats()

        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] > 0
        assert stats["directories"]["debug_photos"]["files"] == 2

    # ============== Delete File Tests ==============

    def test_delete_file_success(self, manager, tmp_path, sample_photo_bytes):
        """Test: delete_file removes existing file."""
        manager.initialize_directories()

        # Create file
        file_path = tmp_path / "debug_photos" / "test.jpg"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(sample_photo_bytes)

        result = manager.delete_file("debug_photos/test.jpg")

        assert result is True
        assert not file_path.exists()

    def test_delete_file_not_found(self, manager, tmp_path):
        """Test: delete_file returns False for non-existing file."""
        manager.initialize_directories()

        result = manager.delete_file("debug_photos/nonexistent.jpg")

        assert result is False


class TestStorageManagerSingleton:
    """Tests for get_storage_manager singleton."""

    def test_singleton_returns_same_instance(self):
        """Test: get_storage_manager returns singleton."""
        # Reset singleton for test
        import app.core.storage as storage_module
        storage_module._storage_manager = None

        manager1 = get_storage_manager()
        manager2 = get_storage_manager()

        assert manager1 is manager2

    def test_singleton_initializes_directories(self, tmp_path):
        """Test: singleton initializes directories."""
        import app.core.storage as storage_module
        storage_module._storage_manager = None

        with patch.object(StorageManager, 'initialize_directories') as mock_init:
            get_storage_manager()
            mock_init.assert_called_once()


class TestCleanupExpiredPhotos:
    """Tests for cleanup_expired_photos async function."""

    @pytest.mark.asyncio
    async def test_cleanup_returns_dict(self):
        """Test: cleanup_expired_photos returns result dict."""
        with patch('app.core.storage.get_storage_manager') as mock_get:
            mock_manager = MagicMock()
            mock_manager.cleanup_expired_files.return_value = (5, 10240)
            mock_get.return_value = mock_manager

            result = await cleanup_expired_photos(dry_run=False)

            assert "files_deleted" in result
            assert "bytes_freed" in result
            assert "dry_run" in result
            assert result["files_deleted"] == 5
            assert result["dry_run"] is False

    @pytest.mark.asyncio
    async def test_cleanup_passes_dry_run(self):
        """Test: cleanup_expired_photos passes dry_run parameter."""
        with patch('app.core.storage.get_storage_manager') as mock_get:
            mock_manager = MagicMock()
            mock_manager.cleanup_expired_files.return_value = (0, 0)
            mock_get.return_value = mock_manager

            await cleanup_expired_photos(dry_run=True)

            mock_manager.cleanup_expired_files.assert_called_once_with(dry_run=True)
