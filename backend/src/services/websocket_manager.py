import asyncio
from typing import Dict, Set

from fastapi import WebSocket
from loguru import logger


class QueueConnectionManager:
    """Manages WebSocket connections for queue updates"""

    def __init__(self):
        # event_id -> {user_id: websocket}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, event_id: int, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        async with self._lock:
            if event_id not in self.active_connections:
                self.active_connections[event_id] = {}

            # Close existing connection for same user/event if any
            if user_id in self.active_connections[event_id]:
                try:
                    await self.active_connections[event_id][user_id].close()
                except Exception:
                    pass

            self.active_connections[event_id][user_id] = websocket

        logger.info(f"WebSocket connected: user {user_id} for event {event_id}")

    async def disconnect(self, event_id: int, user_id: int):
        """Remove a WebSocket connection"""
        async with self._lock:
            if event_id in self.active_connections:
                if user_id in self.active_connections[event_id]:
                    del self.active_connections[event_id][user_id]

                # Clean up empty event dict
                if not self.active_connections[event_id]:
                    del self.active_connections[event_id]

        logger.info(f"WebSocket disconnected: user {user_id} for event {event_id}")

    async def send_to_user(self, event_id: int, user_id: int, message: dict):
        """Send message to a specific user"""
        websocket = None
        async with self._lock:
            if event_id in self.active_connections:
                websocket = self.active_connections[event_id].get(user_id)

        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                await self.disconnect(event_id, user_id)

    async def broadcast_to_event(self, event_id: int, message: dict):
        """Broadcast message to all users in an event queue"""
        users_to_notify = []
        async with self._lock:
            if event_id in self.active_connections:
                users_to_notify = list(self.active_connections[event_id].items())

        disconnected = []
        for user_id, websocket in users_to_notify:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up disconnected
        for user_id in disconnected:
            await self.disconnect(event_id, user_id)

    async def send_position_update(
        self,
        event_id: int,
        user_id: int,
        position: int,
        status: str,
        estimated_wait: int | None,
        total_ahead: int,
        expires_at: str | None,
        can_proceed: bool
    ):
        """Send position update to a user"""
        message = {
            "type": "position_update",
            "data": {
                "position": position,
                "status": status,
                "estimatedWaitMinutes": estimated_wait,
                "totalAhead": total_ahead,
                "expiresAt": expires_at,
                "canProceed": can_proceed,
            }
        }
        await self.send_to_user(event_id, user_id, message)

    async def send_status_change(
        self,
        event_id: int,
        user_id: int,
        old_status: str,
        new_status: str,
        message_text: str,
        redirect_url: str | None = None
    ):
        """Send status change notification to a user"""
        message = {
            "type": "status_change",
            "data": {
                "oldStatus": old_status,
                "newStatus": new_status,
                "message": message_text,
                "redirectUrl": redirect_url,
            }
        }
        await self.send_to_user(event_id, user_id, message)

    async def send_heartbeat(self, event_id: int, user_id: int):
        """Send heartbeat to keep connection alive"""
        message = {"type": "heartbeat", "data": {}}
        await self.send_to_user(event_id, user_id, message)

    def get_connected_users(self, event_id: int) -> Set[int]:
        """Get set of connected user IDs for an event"""
        if event_id in self.active_connections:
            return set(self.active_connections[event_id].keys())
        return set()

    def get_active_event_ids(self) -> Set[int]:
        """Get all event IDs with active connections"""
        return set(self.active_connections.keys())


# Singleton instance
queue_connection_manager = QueueConnectionManager()
