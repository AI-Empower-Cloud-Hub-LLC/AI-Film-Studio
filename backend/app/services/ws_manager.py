"""
WebSocket connection manager for real-time project status updates.
"""
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections grouped by project ID."""

    def __init__(self):
        self._connections: Dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        self._connections.setdefault(project_id, []).append(websocket)
        logger.info(f"WS connected: project={project_id}")

    def disconnect(self, websocket: WebSocket, project_id: str):
        conns = self._connections.get(project_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(project_id, None)
        logger.info(f"WS disconnected: project={project_id}")

    async def broadcast(self, project_id: str, data: Dict[str, Any]):
        message = json.dumps(data)
        dead: list[WebSocket] = []
        for ws in self._connections.get(project_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, project_id)

    async def broadcast_all(self, data: Dict[str, Any]):
        message = json.dumps(data)
        for project_id in list(self._connections):
            dead: list[WebSocket] = []
            for ws in self._connections.get(project_id, []):
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, project_id)


ws_manager = ConnectionManager()
