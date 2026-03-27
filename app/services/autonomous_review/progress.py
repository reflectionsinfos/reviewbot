"""
WebSocket Progress Manager
Broadcasts real-time review progress to connected clients.
"""
import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ProgressManager:
    """Manages WebSocket connections per job and broadcasts progress updates."""

    def __init__(self):
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, job_id: int, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self._connections:
            self._connections[job_id] = []
        self._connections[job_id].append(websocket)
        logger.debug("WS connected for job %s (total: %s)",
                     job_id, len(self._connections[job_id]))

    def disconnect(self, job_id: int, websocket: WebSocket):
        if job_id in self._connections:
            self._connections[job_id] = [
                ws for ws in self._connections[job_id] if ws is not websocket
            ]
            if not self._connections[job_id]:
                del self._connections[job_id]

    async def broadcast(self, job_id: int, message: dict):
        """Send a JSON message to all clients watching this job."""
        if job_id not in self._connections:
            return
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in list(self._connections[job_id]):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(job_id, ws)

    def active_connections(self, job_id: int) -> int:
        return len(self._connections.get(job_id, []))


# Singleton — imported by both orchestrator and the WS route
progress_manager = ProgressManager()
