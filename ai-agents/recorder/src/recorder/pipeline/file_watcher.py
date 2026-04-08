"""OBS folder watcher — monitors for new mp4 segments and enqueues them.

OBS writes 2-minute mp4 segments to a watched folder.
This watcher detects new files, waits for the write to complete (debounce),
then enqueues the file path for processing.
"""

import asyncio
import os
import time
from collections.abc import Callable

import structlog
from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from recorder.core.config import settings

logger = structlog.get_logger()


class _SegmentHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue[str], loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self._queue = queue
        self._loop = loop
        self._pending: dict[str, float] = {}  # path → size last checked

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".mp4"):
            logger.info("segment_detected", path=event.src_path)
            self._loop.call_soon_threadsafe(
                self._loop.create_task,
                self._debounce_and_enqueue(event.src_path),
            )

    async def _debounce_and_enqueue(self, path: str) -> None:
        debounce = settings.file_watcher_debounce_secs
        prev_size = -1
        stable_count = 0
        while stable_count < 2:
            await asyncio.sleep(1)
            try:
                current_size = os.path.getsize(path)
            except OSError:
                return  # file disappeared
            if current_size == prev_size:
                stable_count += 1
            else:
                stable_count = 0
                prev_size = current_size
        logger.info("segment_stable_enqueuing", path=path)
        await self._queue.put(path)


class SegmentWatcher:
    """Watches the OBS output folder and yields stable mp4 file paths."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._observer: Observer | None = None

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        handler = _SegmentHandler(self._queue, loop)
        self._observer = Observer()
        self._observer.schedule(handler, path=settings.obs_watch_folder, recursive=False)
        self._observer.start()
        logger.info("segment_watcher_started", folder=settings.obs_watch_folder)

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("segment_watcher_stopped")

    async def get(self) -> str:
        """Wait for the next stable mp4 segment path."""
        return await self._queue.get()
