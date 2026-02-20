# WebSocket route for real-time queue position updates.
# Provides a persistent connection so the frontend can display live queue movement
# without polling the REST API.
import fastapi
from fastapi import WebSocket, WebSocketDisconnect, Query
from loguru import logger

from src.config.manager import settings
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository
from src.repository.events import async_db_session
from src.services.websocket_manager import queue_connection_manager
from src.services.queue_service import queue_service
from src.securities.authorizations.jwt import jwt_generator

router = fastapi.APIRouter(tags=["websocket"])


# Extracts and validates a JWT token to identify the connecting user.
# WebSockets cannot use standard HTTP auth headers easily, so the token
# is passed as a query parameter instead.
async def get_user_id_from_token(token: str) -> int | None:
    """Validate JWT token and return user ID."""
    try:
        # Decode the JWT to extract the username and email claims
        username, email = jwt_generator.retrieve_details_from_token(
            token=token, secret_key=settings.JWT_SECRET_KEY
        )
        # Look up the account in the database to get the numeric user ID
        async with async_db_session() as session:
            account_repo = AccountCRUDRepository(async_session=session)
            account = await account_repo.read_account_by_username(username=username)
            # Reject blocked accounts even if the token is valid
            if account and not account.is_blocked:
                return account.id
        return None
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


# --- WS /ws/queue/{event_id}?token=<jwt> ---
# Establishes a WebSocket connection for a user to receive real-time queue position updates.
# Flow:
#   1. Accept the connection (required before sending error responses)
#   2. Validate the JWT token passed as a query parameter
#   3. Register the connection in the connection manager (one per user per event)
#   4. Send the initial queue position immediately
#   5. Listen for "refresh" messages from the client to push updated positions
#   6. Clean up on disconnect or error
@router.websocket("/ws/queue/{event_id}")
async def queue_websocket(
    websocket: WebSocket,
    event_id: int,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time queue position updates."""
    # Must accept before sending any data or closing with a custom code
    await websocket.accept()

    # Authenticate the user via the JWT token query parameter
    user_id = await get_user_id_from_token(token)
    if not user_id:
        # Send an error message before closing so the client knows why
        await websocket.send_json({"type": "error", "data": {"message": "Invalid token"}})
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Register this WebSocket in the connection manager, keyed by event_id and user_id.
    # If the same user reconnects, close their previous connection to avoid duplicates.
    async with queue_connection_manager._lock:
        if event_id not in queue_connection_manager.active_connections:
            queue_connection_manager.active_connections[event_id] = {}

        # Close any existing connection for the same user on this event
        if user_id in queue_connection_manager.active_connections[event_id]:
            try:
                await queue_connection_manager.active_connections[event_id][user_id].close()
            except Exception:
                pass

        queue_connection_manager.active_connections[event_id][user_id] = websocket

    logger.info(f"WebSocket connected: user {user_id} for event {event_id}")

    try:
        # Send the user's current queue position immediately upon connection
        try:
            async with async_db_session() as session:
                queue_repo = QueueCRUDRepository(async_session=session)
                event_repo = EventCRUDRepository(async_session=session)

                # Fetch the user's live position data from the queue service
                position_data = await queue_service.get_position(
                    queue_repo=queue_repo,
                    event_repo=event_repo,
                    event_id=event_id,
                    user_id=user_id,
                )

                if position_data:
                    # Convert the expires_at datetime to ISO string for JSON serialization
                    expires_at_str = None
                    if position_data.get("expires_at"):
                        expires_at_str = position_data["expires_at"].isoformat()

                    # Push the position update to this specific user's WebSocket
                    await queue_connection_manager.send_position_update(
                        event_id=event_id,
                        user_id=user_id,
                        position=position_data["position"],
                        status=position_data["status"],
                        estimated_wait=position_data.get("estimated_wait_minutes"),
                        total_ahead=position_data["total_ahead"],
                        expires_at=expires_at_str,
                        can_proceed=position_data.get("can_proceed", False),
                    )
                else:
                    # User connected but is not in the queue for this event
                    logger.warning(f"User {user_id} not in queue for event {event_id}")
        except Exception as e:
            logger.error(f"Error fetching initial position: {e}")
            await websocket.send_json({"type": "error", "data": {"message": "Failed to fetch queue position"}})

        # Main message loop: keep the connection alive and handle client-initiated messages
        while True:
            # Block until the client sends a JSON message
            data = await websocket.receive_json()

            # Handle "refresh" messages: the client requests an updated position
            if data.get("type") == "refresh":
                async with async_db_session() as session:
                    queue_repo = QueueCRUDRepository(async_session=session)
                    event_repo = EventCRUDRepository(async_session=session)

                    # Re-fetch the latest position data
                    position_data = await queue_service.get_position(
                        queue_repo=queue_repo,
                        event_repo=event_repo,
                        event_id=event_id,
                        user_id=user_id,
                    )

                    if position_data:
                        expires_at_str = None
                        if position_data.get("expires_at"):
                            expires_at_str = position_data["expires_at"].isoformat()

                        # Send the refreshed position to the client
                        await queue_connection_manager.send_position_update(
                            event_id=event_id,
                            user_id=user_id,
                            position=position_data["position"],
                            status=position_data["status"],
                            estimated_wait=position_data.get("estimated_wait_minutes"),
                            total_ahead=position_data["total_ahead"],
                            expires_at=expires_at_str,
                            can_proceed=position_data.get("can_proceed", False),
                        )
                    else:
                        # User left the queue or was removed while connected
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Not in queue"}
                        })

    except WebSocketDisconnect:
        # Clean disconnect: remove the connection from the manager
        await queue_connection_manager.disconnect(event_id, user_id)
        logger.info(f"WebSocket disconnected: user {user_id} for event {event_id}")
    except Exception as e:
        # Unexpected error: log and clean up the connection
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await queue_connection_manager.disconnect(event_id, user_id)
