"""
Background tasks for the application.
Handles scheduled cleanup and maintenance operations.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks for the application.
    Runs cleanup tasks on a schedule.
    """

    def __init__(self):
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        # Run cleanup every 6 hours
        self._cleanup_interval_hours = 6

    async def start(self) -> None:
        """Start background tasks."""
        if self._running:
            logger.warning("Background tasks already running")
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Background task manager started")

    async def stop(self) -> None:
        """Stop background tasks."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        logger.info("Background task manager stopped")

    async def _cleanup_loop(self) -> None:
        """
        Main cleanup loop.
        Runs storage cleanup on a schedule.
        """
        # Import here to avoid circular imports
        from app.core.storage import get_storage_manager

        # Run initial cleanup after 1 minute
        await asyncio.sleep(60)

        while self._running:
            try:
                logger.info("Starting scheduled cleanup...")
                manager = get_storage_manager()
                files_deleted, bytes_freed = manager.cleanup_expired_files()

                logger.info(
                    f"Scheduled cleanup completed: {files_deleted} files, "
                    f"{bytes_freed / 1024 / 1024:.2f} MB freed"
                )

            except Exception as e:
                logger.error(f"Error during scheduled cleanup: {e}")

            # Wait for next cleanup cycle
            await asyncio.sleep(self._cleanup_interval_hours * 3600)

    async def run_cleanup_now(self, dry_run: bool = False) -> dict:
        """
        Run cleanup immediately (manual trigger).

        Args:
            dry_run: If True, only report without deleting

        Returns:
            Cleanup results
        """
        from app.core.storage import cleanup_expired_photos

        logger.info(f"Manual cleanup triggered (dry_run={dry_run})")
        result = await cleanup_expired_photos(dry_run=dry_run)
        logger.info(f"Manual cleanup completed: {result}")
        return result


# Singleton instance
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Get singleton instance of BackgroundTaskManager."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager


async def start_background_tasks() -> None:
    """Start all background tasks. Called from app lifespan."""
    manager = get_task_manager()
    await manager.start()


async def stop_background_tasks() -> None:
    """Stop all background tasks. Called from app lifespan."""
    manager = get_task_manager()
    await manager.stop()
