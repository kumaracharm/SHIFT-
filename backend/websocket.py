"""
DRIFTGUARD 2.0 Real-Time WebSocket Manager
Manages real-time WebSocket client connections and event broadcasting.
"""

from typing import List, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger("driftguard.websocket")


class ConnectionManager:
    """Manages active WebSocket client connections for real-time telemetry streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON-serializable message to all active clients."""
        if not self.active_connections:
            return

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client, marking for removal: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)


ws_manager = ConnectionManager()

