import asyncio
from typing import Dict, Set

from fastapi import WebSocket
from loguru import logger


# Manages WebSocket connections for real-time queue position updates to users
class QueueConnectionManager:
    """Manages WebSocket connections for queue updates"""

    def __init__(self):
        # Nested dict mapping event_id -> {user_id: websocket} for active connections
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # Asyncio lock to ensure thread-safe access to the connections dict
        self._lock = asyncio.Lock()

    # Accept a new WebSocket connection, closing any existing connection for the same user/event
    async def connect(self, websocket: WebSocket, event_id: int, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        async with self._lock:
            # Create a new dict for this event if none exists yet
            if event_id not in self.active_connections:
                self.active_connections[event_id] = {}

            # Close any previous connection for this user on the same event to avoid duplicates
            if user_id in self.active_connections[event_id]:
                try:
                    await self.active_connections[event_id][user_id].close()
                except Exception:
                    pass

            # Store the new WebSocket connection
            self.active_connections[event_id][user_id] = websocket

        logger.info(f"WebSocket connected: user {user_id} for event {event_id}")

    # Remove and clean up a WebSocket connection for a specific user and event
    async def disconnect(self, event_id: int, user_id: int):
        """Remove a WebSocket connection"""
        async with self._lock:
            if event_id in self.active_connections:
                if user_id in self.active_connections[event_id]:
                    del self.active_connections[event_id][user_id]

                # Remove the event entry entirely if no users remain connected
                if not self.active_connections[event_id]:
                    del self.active_connections[event_id]

        logger.info(f"WebSocket disconnected: user {user_id} for event {event_id}")

    # Send a JSON message to a single user; disconnects the user if sending fails
    async def send_to_user(self, event_id: int, user_id: int, message: dict):
        """Send message to a specific user"""
        websocket = None
        # Retrieve the websocket reference under lock, then send outside the lock
        async with self._lock:
            if event_id in self.active_connections:
                websocket = self.active_connections[event_id].get(user_id)

        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                # On send failure, clean up the broken connection
                logger.error(f"Failed to send to user {user_id}: {e}")
                await self.disconnect(event_id, user_id)

    # Broadcast a JSON message to all connected users for a given event
    async def broadcast_to_event(self, event_id: int, message: dict):
        """Broadcast message to all users in an event queue"""
        # Snapshot the current connections under lock
        users_to_notify = []
        async with self._lock:
            if event_id in self.active_connections:
                users_to_notify = list(self.active_connections[event_id].items())

        # Send to each user and track failures
        disconnected = []
        for user_id, websocket in users_to_notify:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected.append(user_id)

        # Clean up all connections that failed during broadcast
        for user_id in disconnected:
            await self.disconnect(event_id, user_id)

    # Send a position update message containing queue position, status, and wait estimate
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
        # Build a structured message with type and data payload for the frontend
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

    # Notify a user when their queue status changes (e.g., waiting -> processing)
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

    # Send a heartbeat message to keep the WebSocket connection alive and prevent timeout
    async def send_heartbeat(self, event_id: int, user_id: int):
        """Send heartbeat to keep connection alive"""
        message = {"type": "heartbeat", "data": {}}
        await self.send_to_user(event_id, user_id, message)

    # Return the set of user IDs currently connected via WebSocket for a specific event
    def get_connected_users(self, event_id: int) -> Set[int]:
        """Get set of connected user IDs for an event"""
        if event_id in self.active_connections:
            return set(self.active_connections[event_id].keys())
        return set()

    # Return all event IDs that have at least one active WebSocket connection
    def get_active_event_ids(self) -> Set[int]:
        """Get all event IDs with active connections"""
        return set(self.active_connections.keys())


# Singleton instance — shared across the application for WebSocket connection management
queue_connection_manager = QueueConnectionManager()
