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


async def get_user_id_from_token(token: str) -> int | None:
    """Validate JWT token and return user ID."""
    try:
        username, email = jwt_generator.retrieve_details_from_token(
            token=token, secret_key=settings.JWT_SECRET_KEY
        )
        # Look up user by username to get ID
        async with async_db_session() as session:
            account_repo = AccountCRUDRepository(async_session=session)
            account = await account_repo.read_account_by_username(username=username)
            if account and not account.is_blocked:
                return account.id
        return None
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


@router.websocket("/ws/queue/{event_id}")
async def queue_websocket(
    websocket: WebSocket,
    event_id: int,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time queue position updates."""
    # Accept connection first (required for proper error handling)
    await websocket.accept()

    # Validate token
    user_id = await get_user_id_from_token(token)
    if not user_id:
        await websocket.send_json({"type": "error", "data": {"message": "Invalid token"}})
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Register connection
    async with queue_connection_manager._lock:
        if event_id not in queue_connection_manager.active_connections:
            queue_connection_manager.active_connections[event_id] = {}

        # Close existing connection for same user/event if any
        if user_id in queue_connection_manager.active_connections[event_id]:
            try:
                await queue_connection_manager.active_connections[event_id][user_id].close()
            except Exception:
                pass

        queue_connection_manager.active_connections[event_id][user_id] = websocket

    logger.info(f"WebSocket connected: user {user_id} for event {event_id}")

    try:
        # Send initial position
        try:
            async with async_db_session() as session:
                queue_repo = QueueCRUDRepository(async_session=session)
                event_repo = EventCRUDRepository(async_session=session)

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
                    logger.warning(f"User {user_id} not in queue for event {event_id}")
        except Exception as e:
            logger.error(f"Error fetching initial position: {e}")
            await websocket.send_json({"type": "error", "data": {"message": "Failed to fetch queue position"}})

        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()

            # Handle client messages
            if data.get("type") == "refresh":
                # Client requesting position update
                async with async_db_session() as session:
                    queue_repo = QueueCRUDRepository(async_session=session)
                    event_repo = EventCRUDRepository(async_session=session)

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
                        # User no longer in queue
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Not in queue"}
                        })

    except WebSocketDisconnect:
        await queue_connection_manager.disconnect(event_id, user_id)
        logger.info(f"WebSocket disconnected: user {user_id} for event {event_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await queue_connection_manager.disconnect(event_id, user_id)
