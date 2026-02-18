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
        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

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
        raise HTTPException(status_code=404, detail="Event not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        result = await queue_service.get_position(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
            user_id=current_user.id,
        )

        if not result:
            raise HTTPException(status_code=404, detail="Not in queue")

        return QueuePositionResponse(**result)

    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Event not found")


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
    success = await queue_repo.leave_queue(
        event_id=event_id,
        user_id=current_user.id,
    )

    if success:
        return QueueLeaveResponse(success=True, message="Successfully left the queue")
    else:
        return QueueLeaveResponse(success=False, message="Not in queue")


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
        result = await queue_service.get_queue_status(
            queue_repo=queue_repo,
            event_repo=event_repo,
            event_id=event_id,
        )

        return QueueStatusResponse(**result)

    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Event not found")
