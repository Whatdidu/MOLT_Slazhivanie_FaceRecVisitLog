"""
Camera module - FTP сервер для приёма снапшотов с камеры.
Камера отправляет снапшоты при событиях, сервер принимает и запускает распознавание.
"""

from .ftp_server import start_ftp_server, stop_ftp_server
from .snapshot_handler import process_snapshot

__all__ = ["start_ftp_server", "stop_ftp_server", "process_snapshot"]
