"""
FTP сервер для приёма снапшотов с IP камеры.
Камера отправляет снапшоты при событиях (motion detect, intrusion и т.д.)
При загрузке файла автоматически запускает распознавание лица.
"""

import asyncio
import os
from pathlib import Path
from threading import Thread

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Глобальная ссылка на сервер для остановки
_ftp_server: FTPServer | None = None
_ftp_thread: Thread | None = None

# Callback для обработки новых файлов
_on_file_received = None
_event_loop = None


class SnapshotFTPHandler(FTPHandler):
    """FTP Handler с callback при завершении загрузки файла."""

    def on_file_received(self, file: str):
        """Вызывается когда файл полностью загружен."""
        logger.info(f"Snapshot received via FTP: {file}")

        if _on_file_received and _event_loop:
            # Запускаем обработку в asyncio event loop
            asyncio.run_coroutine_threadsafe(
                _on_file_received(file),
                _event_loop
            )


def _create_ftp_server() -> FTPServer:
    """Создаёт и настраивает FTP сервер."""
    # Создаём директорию для снапшотов
    snapshots_dir = Path(settings.ftp_snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Настраиваем авторизацию
    authorizer = DummyAuthorizer()
    authorizer.add_user(
        settings.ftp_user,
        settings.ftp_password,
        str(snapshots_dir.absolute()),
        perm="elradfmw"  # Все права на запись
    )

    # Настраиваем handler
    handler = SnapshotFTPHandler
    handler.authorizer = authorizer
    handler.passive_ports = range(60000, 60011)  # 60000-60010 for Docker

    # Настраиваем external IP для passive mode (важно для NAT/облака)
    if settings.ftp_passive_address:
        handler.masquerade_address = settings.ftp_passive_address

    # Создаём сервер
    server = FTPServer(
        (settings.ftp_host, settings.ftp_port),
        handler
    )
    server.max_cons = 10
    server.max_cons_per_ip = 5

    return server


def _run_ftp_server(server: FTPServer):
    """Запускает FTP сервер в отдельном потоке."""
    try:
        server.serve_forever()
    except Exception as e:
        logger.error(f"FTP server error: {e}")


async def start_ftp_server(on_file_callback=None):
    """
    Запускает FTP сервер в фоновом потоке.

    Args:
        on_file_callback: async функция, вызываемая при получении файла.
                         Сигнатура: async def callback(file_path: str)
    """
    global _ftp_server, _ftp_thread, _on_file_received, _event_loop

    if not settings.ftp_enabled:
        logger.info("FTP server disabled in config")
        return

    if _ftp_server is not None:
        logger.warning("FTP server already running")
        return

    _on_file_received = on_file_callback
    _event_loop = asyncio.get_running_loop()
    _ftp_server = _create_ftp_server()

    _ftp_thread = Thread(target=_run_ftp_server, args=(_ftp_server,), daemon=True)
    _ftp_thread.start()

    logger.info(
        f"FTP server started on {settings.ftp_host}:{settings.ftp_port} "
        f"(user: {settings.ftp_user}, dir: {settings.ftp_snapshots_dir})"
    )
    if settings.ftp_passive_address:
        logger.info(f"FTP passive address: {settings.ftp_passive_address}")


async def stop_ftp_server():
    """Останавливает FTP сервер."""
    global _ftp_server, _ftp_thread

    if _ftp_server is not None:
        _ftp_server.close_all()
        _ftp_server = None
        logger.info("FTP server stopped")

    _ftp_thread = None
