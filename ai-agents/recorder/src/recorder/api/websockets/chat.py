"""WebSocket handler for live chat during meetings.

Clients connect to /ws/sessions/{session_id}/chat to receive:
  - Agent responses to queries
  - Inter-agent conflict alerts
  - Meeting health monitor alerts
  - Transcript chunk summaries

Phase 1: text chat only
Phase 3+: voice query results streamed back
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, list[WebSocket]] = {}  # session_id → [ws]

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self.active.setdefault(session_id, []).append(ws)
        logger.info("ws_connected", session_id=session_id)

    def disconnect(self, session_id: str, ws: WebSocket) -> None:
        if session_id in self.active:
            self.active[session_id].discard(ws)
        logger.info("ws_disconnected", session_id=session_id)

    async def broadcast(self, session_id: str, message: dict) -> None:
        for ws in list(self.active.get(session_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/sessions/{session_id}/chat")
async def chat_ws(session_id: str, websocket: WebSocket) -> None:
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Phase 1: echo back; Phase 3+: route to orchestrator
            await websocket.send_json({
                "type": "agent_response",
                "session_id": session_id,
                "question": data.get("text", ""),
                "answer": "[Phase 1 MVP — agent implementation pending]",
                "responding_agent": "Default Expert",
            })
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
