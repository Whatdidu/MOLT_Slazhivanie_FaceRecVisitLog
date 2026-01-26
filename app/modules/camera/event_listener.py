"""
TCP Event Listener для камеры.
Подключается к порту событий камеры и слушает alarm events.
При получении события делает RTSP снапшот.
"""

import asyncio
import re
from pathlib import Path

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Глобальные переменные для управления listener'ом
_listener_task: asyncio.Task | None = None
_should_stop = False

# Callback для обработки снапшотов
_on_snapshot_callback = None


async def _capture_rtsp_snapshot() -> str | None:
    """
    Делает снапшот с RTSP потока камеры через ffmpeg.

    Returns:
        Путь к файлу снапшота или None при ошибке
    """
    import subprocess
    from datetime import datetime

    # Создаём директорию для снапшотов
    snapshots_dir = Path(settings.camera_snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    snapshot_path = snapshots_dir / f"snapshot_{timestamp}.jpg"

    # RTSP URL
    rtsp_url = (
        f"rtsp://{settings.camera_user}:{settings.camera_password}@"
        f"{settings.camera_ip}:{settings.camera_rtsp_port}/stream1"
    )

    # ffmpeg команда
    cmd = [
        "ffmpeg", "-y",
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-frames:v", "1",
        "-update", "1",
        str(snapshot_path)
    ]

    try:
        # Запускаем ffmpeg асинхронно
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.wait_for(process.wait(), timeout=10.0)

        if snapshot_path.exists() and snapshot_path.stat().st_size > 1000:
            logger.info(f"Snapshot captured: {snapshot_path}")
            return str(snapshot_path)
        else:
            logger.warning("Snapshot file is empty or too small")
            return None

    except asyncio.TimeoutError:
        logger.error("ffmpeg timeout while capturing snapshot")
        process.kill()
        return None
    except Exception as e:
        logger.error(f"Failed to capture snapshot: {e}")
        return None


async def _parse_alarm_event(data: bytes) -> dict | None:
    """
    Парсит XML событие от камеры.

    Returns:
        Словарь с данными события или None
    """
    try:
        text = data.decode('gb2312', errors='ignore')

        # Проверяем что это alarm event
        if 'ALARM_REPORT_MESSAGE' not in text:
            return None

        # Извлекаем данные
        event = {
            'type': 'alarm',
            'code': None,
            'flag': None,
            'data': None,
        }

        # Парсим Alarm_code
        match = re.search(r'Alarm_code="(\d+)"', text)
        if match:
            event['code'] = match.group(1)

        # Парсим Alarm_flag
        match = re.search(r'Alarm_flag="(\d+)"', text)
        if match:
            event['flag'] = match.group(1)

        # Парсим Alarm_data
        match = re.search(r'Alarm_data="([^"]*)"', text)
        if match:
            event['data'] = match.group(1)

        return event

    except Exception as e:
        logger.debug(f"Failed to parse event: {e}")
        return None


async def _event_listener_loop():
    """
    Основной цикл слушателя событий.
    Подключается к камере и обрабатывает события.
    """
    global _should_stop

    reconnect_delay = 5  # секунд между попытками реконнекта

    while not _should_stop:
        try:
            logger.info(
                f"Connecting to camera event stream: "
                f"{settings.camera_ip}:{settings.camera_event_port}"
            )

            reader, writer = await asyncio.open_connection(
                settings.camera_ip,
                settings.camera_event_port
            )

            logger.info("Connected to camera event stream")
            reconnect_delay = 5  # сброс задержки при успешном подключении

            buffer = b""

            while not _should_stop:
                try:
                    # Читаем данные
                    data = await asyncio.wait_for(
                        reader.read(4096),
                        timeout=60.0  # keepalive timeout
                    )

                    if not data:
                        logger.warning("Camera connection closed")
                        break

                    buffer += data

                    # Ищем завершённые XML сообщения
                    while b'</XML_TOPSEE>' in buffer:
                        end_idx = buffer.find(b'</XML_TOPSEE>') + len(b'</XML_TOPSEE>')
                        message = buffer[:end_idx]
                        buffer = buffer[end_idx:]

                        # Парсим событие
                        event = await _parse_alarm_event(message)

                        if event and event.get('flag') == '1':
                            logger.info(f"Alarm event received: {event}")

                            # Делаем снапшот
                            snapshot_path = await _capture_rtsp_snapshot()

                            if snapshot_path and _on_snapshot_callback:
                                # Вызываем callback для обработки
                                asyncio.create_task(
                                    _on_snapshot_callback(snapshot_path)
                                )

                except asyncio.TimeoutError:
                    # Нет данных 60 секунд - отправляем keepalive или просто продолжаем
                    continue

        except ConnectionRefusedError:
            logger.warning(
                f"Camera connection refused. Retrying in {reconnect_delay}s..."
            )
        except Exception as e:
            logger.error(f"Camera listener error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

        if not _should_stop:
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)  # exponential backoff


async def start_camera_listener(on_snapshot_callback=None):
    """
    Запускает слушатель событий камеры.

    Args:
        on_snapshot_callback: async функция, вызываемая при получении снапшота.
                             Сигнатура: async def callback(file_path: str)
    """
    global _listener_task, _should_stop, _on_snapshot_callback

    if not settings.camera_enabled:
        logger.info("Camera listener disabled in config")
        return

    if _listener_task is not None:
        logger.warning("Camera listener already running")
        return

    _should_stop = False
    _on_snapshot_callback = on_snapshot_callback
    _listener_task = asyncio.create_task(_event_listener_loop())

    logger.info(
        f"Camera listener started for {settings.camera_ip}:{settings.camera_event_port}"
    )


async def stop_camera_listener():
    """Останавливает слушатель событий камеры."""
    global _listener_task, _should_stop

    _should_stop = True

    if _listener_task is not None:
        _listener_task.cancel()
        try:
            await _listener_task
        except asyncio.CancelledError:
            pass
        _listener_task = None

    logger.info("Camera listener stopped")
