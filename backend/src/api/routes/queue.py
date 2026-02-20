# Queue routes: manage virtual queues for high-demand events.
# Users join a queue, check their position, and are granted booking access in batches.
import fastapi
from fastapi import Depends, HTTPException, Request

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.queue import (
    QueueJoinResponse,
    QueuePositionResponse,
    QueueStatusResponse,
    QueueLeaveResponse,
)
from src.repository.crud.queue import QueueCRUDRepository
from src.repository.crud.event import EventCRUDRepository
from src.services.queue_service import queue_service
from src.utilities.exceptions.database import EntityDoesNotExist

router = fastapi.APIRouter(prefix="/queue", tags=["queue"])


# --- POST /queue/{event_id}/join ---
# Adds the authenticated user to the virtual queue for a given event.
# Captures client metadata (IP address, user agent) for fraud detection and analytics.
# Returns the user's assigned queue position and estimated wait time.
@router.post(
    "/{event_id}/join",
    name="queue:join",
    response_model=QueueJoinResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def join_queue(
    event_id: int,
    request: Request,
    current_user: Account = Depends(get_current_user),
    queue_repo: QueueCRUDRepository = Depends(get_repository(repo_type=QueueCRUDRepository)),
    event_repo: EventCRUDRepository = Depends(get_repository(repo_type=EventCRUDRepository)),
) -> QueueJoinResponse:
    """Join the queue for an event."""
    try:
        # Extract client connection info for tracking and abuse prevention
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Delegate to the queue service which handles position assignment and duplicate checks
        result = await queue_service.join_queue(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return QueueJoinResponse(**result)

    except EntityDoesNotExist:
        # The specified event does not exist in the database
        raise HTTPException(status_code=404, detail="Event not found")
    except ValueError as e:
        # Business rule violation (e.g., queue not enabled, event not open for booking)
        raise HTTPException(status_code=400, detail=str(e))


# --- GET /queue/{event_id}/position ---
# Returns the current user's position in the event queue, including
# how many people are ahead and the estimated wait time in minutes.
# Returns 404 if the user has not joined the queue.
@router.get(
    "/{event_id}/position",
    name="queue:position",
    response_model=QueuePositionResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_position(
    event_id: int,
    current_user: Account = Depends(get_current_user),
    queue_repo: QueueCRUDRepository = Depends(get_repository(repo_type=QueueCRUDRepository)),
    event_repo: EventCRUDRepository = Depends(get_repository(repo_type=EventCRUDRepository)),
) -> QueuePositionResponse:
    """Get the current user's position in the queue."""
    try:
        # Fetch the user's queue entry and compute their live position
        result = await queue_service.get_position(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
            user_id=current_user.id,
        )

        # If result is None, the user is not currently in the queue
        if not result:
            raise HTTPException(status_code=404, detail="Not in queue")

        return QueuePositionResponse(**result)

    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Event not found")


# --- DELETE /queue/{event_id}/leave ---
# Removes the current user from the event queue voluntarily.
# Returns success status indicating whether the user was actually in the queue.
@router.delete(
    "/{event_id}/leave",
    name="queue:leave",
    response_model=QueueLeaveResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def leave_queue(
    event_id: int,
    current_user: Account = Depends(get_current_user),
    queue_repo: QueueCRUDRepository = Depends(get_repository(repo_type=QueueCRUDRepository)),
) -> QueueLeaveResponse:
    """Leave the queue for an event."""
    # Attempt to remove the user's queue entry; returns False if not found
    success = await queue_repo.leave_queue(
        event_id=event_id,
        user_id=current_user.id,
    )

    if success:
        return QueueLeaveResponse(success=True, message="Successfully left the queue")
    else:
        # User was not in the queue, so there is nothing to remove
        return QueueLeaveResponse(success=False, message="Not in queue")


# --- GET /queue/{event_id}/status ---
# Public endpoint (no authentication required) that returns aggregate queue statistics
# for an event, such as total users in queue and current processing status.
# Useful for displaying queue info on the event page before login.
@router.get(
    "/{event_id}/status",
    name="queue:status",
    response_model=QueueStatusResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_queue_status(
    event_id: int,
    queue_repo: QueueCRUDRepository = Depends(get_repository(repo_type=QueueCRUDRepository)),
    event_repo: EventCRUDRepository = Depends(get_repository(repo_type=EventCRUDRepository)),
) -> QueueStatusResponse:
    """Get the public queue status for an event (no auth required)."""
    try:
        # Retrieve aggregate queue metrics from the queue service
        result = await queue_service.get_queue_status(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
        )

        return QueueStatusResponse(**result)

    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Event not found")
