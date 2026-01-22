"""
Storage management utilities with TTL support.
Handles file cleanup for debug photos and temporary storage.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manages file storage with TTL (Time To Live) support.

    Directory structure:
    app/static/
    ├── debug_photos/           # Camera snapshots (TTL: 7 days)
    │   └── YYYY-MM-DD/         # Organized by date
    │       └── {trace_id}.jpg
    └── employee_photos/        # Employee enrollment photos
        └── {email}_{timestamp}_{uuid}.jpg
    """

    def __init__(
        self,
        base_path: Optional[str] = None,
        default_ttl_days: Optional[int] = None,
    ):
        """
        Initialize storage manager.

        Args:
            base_path: Base storage path (default: settings.static_path)
            default_ttl_days: Default TTL in days (default: settings.debug_photos_ttl_days)
        """
        self.base_path = Path(base_path or settings.static_path)
        self.default_ttl_days = default_ttl_days or settings.debug_photos_ttl_days

        # Directory names
        self.debug_photos_dir = "debug_photos"
        self.employee_photos_dir = "employee_photos"

    def initialize_directories(self) -> None:
        """Create necessary directory structure."""
        directories = [
            self.base_path / self.debug_photos_dir,
            self.base_path / self.employee_photos_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")

    def get_debug_photos_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get path for debug photos directory, organized by date.

        Args:
            date: Date for subdirectory (default: today)

        Returns:
            Path to debug photos directory for the given date
        """
        if date is None:
            date = datetime.utcnow()

        date_str = date.strftime("%Y-%m-%d")
        path = self.base_path / self.debug_photos_dir / date_str
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_debug_photo(
        self,
        photo_bytes: bytes,
        trace_id: str,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Save a debug photo (camera snapshot).

        Args:
            photo_bytes: Photo data
            trace_id: Unique trace ID for the request
            timestamp: Timestamp for organizing (default: now)

        Returns:
            Relative path to saved photo
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Get directory for this date
        photo_dir = self.get_debug_photos_path(timestamp)

        # Create filename with timestamp and trace_id
        time_str = timestamp.strftime("%H%M%S")
        filename = f"{time_str}_{trace_id}.jpg"
        file_path = photo_dir / filename

        # Save photo
        file_path.write_bytes(photo_bytes)
        logger.debug(f"Saved debug photo: {file_path}")

        # Return relative path from static directory
        return str(file_path.relative_to(self.base_path))

    def cleanup_expired_files(
        self,
        directory: Optional[str] = None,
        ttl_days: Optional[int] = None,
        dry_run: bool = False,
    ) -> tuple[int, int]:
        """
        Remove files older than TTL.

        Args:
            directory: Directory to clean (default: debug_photos)
            ttl_days: TTL in days (default: settings.debug_photos_ttl_days)
            dry_run: If True, only report without deleting

        Returns:
            Tuple of (files_deleted, bytes_freed)
        """
        if directory is None:
            directory = self.debug_photos_dir
        if ttl_days is None:
            ttl_days = self.default_ttl_days

        target_path = self.base_path / directory
        if not target_path.exists():
            logger.warning(f"Directory does not exist: {target_path}")
            return 0, 0

        cutoff_date = datetime.utcnow() - timedelta(days=ttl_days)
        files_deleted = 0
        bytes_freed = 0

        logger.info(
            f"Starting cleanup: {target_path}, TTL={ttl_days} days, "
            f"cutoff={cutoff_date.isoformat()}, dry_run={dry_run}"
        )

        # Walk through directory
        for item in target_path.rglob("*"):
            if not item.is_file():
                continue

            # Skip .gitkeep files
            if item.name == ".gitkeep":
                continue

            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(item.stat().st_mtime)

                if mtime < cutoff_date:
                    file_size = item.stat().st_size

                    if dry_run:
                        logger.info(f"Would delete (dry run): {item} (modified: {mtime})")
                    else:
                        item.unlink()
                        logger.debug(f"Deleted: {item}")

                    files_deleted += 1
                    bytes_freed += file_size

            except OSError as e:
                logger.error(f"Error processing {item}: {e}")

        # Cleanup empty date directories
        if not dry_run:
            self._cleanup_empty_directories(target_path)

        logger.info(
            f"Cleanup complete: {files_deleted} files, "
            f"{bytes_freed / 1024 / 1024:.2f} MB freed"
        )

        return files_deleted, bytes_freed

    def _cleanup_empty_directories(self, root_path: Path) -> int:
        """
        Remove empty subdirectories.

        Args:
            root_path: Root path to clean

        Returns:
            Number of directories removed
        """
        dirs_removed = 0

        # Get all subdirectories, sorted by depth (deepest first)
        subdirs = sorted(
            [d for d in root_path.rglob("*") if d.is_dir()],
            key=lambda p: len(p.parts),
            reverse=True,
        )

        for subdir in subdirs:
            try:
                # Check if directory is empty (only .gitkeep or nothing)
                contents = list(subdir.iterdir())
                if not contents or (len(contents) == 1 and contents[0].name == ".gitkeep"):
                    # Keep the root debug_photos directory
                    if subdir != root_path:
                        # Remove .gitkeep if present
                        gitkeep = subdir / ".gitkeep"
                        if gitkeep.exists():
                            gitkeep.unlink()
                        subdir.rmdir()
                        dirs_removed += 1
                        logger.debug(f"Removed empty directory: {subdir}")
            except OSError as e:
                logger.error(f"Error removing directory {subdir}: {e}")

        return dirs_removed

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "base_path": str(self.base_path),
            "directories": {},
            "total_files": 0,
            "total_size_bytes": 0,
        }

        for dir_name in [self.debug_photos_dir, self.employee_photos_dir]:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                stats["directories"][dir_name] = {
                    "exists": False,
                    "files": 0,
                    "size_bytes": 0,
                }
                continue

            files = list(dir_path.rglob("*"))
            files = [f for f in files if f.is_file() and f.name != ".gitkeep"]
            total_size = sum(f.stat().st_size for f in files)

            stats["directories"][dir_name] = {
                "exists": True,
                "files": len(files),
                "size_bytes": total_size,
                "size_mb": round(total_size / 1024 / 1024, 2),
            }

            stats["total_files"] += len(files)
            stats["total_size_bytes"] += total_size

        stats["total_size_mb"] = round(stats["total_size_bytes"] / 1024 / 1024, 2)

        return stats

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a specific file.

        Args:
            relative_path: Path relative to base_path

        Returns:
            True if deleted, False if not found
        """
        file_path = self.base_path / relative_path
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
            return True
        return False


# Singleton instance
_storage_manager: StorageManager | None = None


def get_storage_manager() -> StorageManager:
    """Get singleton instance of StorageManager."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager()
        _storage_manager.initialize_directories()
    return _storage_manager


async def cleanup_expired_photos(dry_run: bool = False) -> dict:
    """
    Async wrapper for cleanup task.
    Can be called from background scheduler or manually.

    Args:
        dry_run: If True, only report without deleting

    Returns:
        Cleanup results
    """
    manager = get_storage_manager()
    files_deleted, bytes_freed = manager.cleanup_expired_files(dry_run=dry_run)

    return {
        "files_deleted": files_deleted,
        "bytes_freed": bytes_freed,
        "bytes_freed_mb": round(bytes_freed / 1024 / 1024, 2),
        "dry_run": dry_run,
    }
