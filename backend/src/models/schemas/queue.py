import datetime
from uuid import UUID

from src.models.schemas.base import BaseSchemaModel


class QueueJoinRequest(BaseSchemaModel):
    """Request to join a queue - event_id comes from path parameter"""
    pass


class QueueJoinResponse(BaseSchemaModel):
    """Response when joining a queue"""
    queue_entry_id: UUID
    event_id: int
    position: int
    status: str
    estimated_wait_minutes: int | None = None
    total_ahead: int
    joined_at: datetime.datetime


class QueuePositionResponse(BaseSchemaModel):
    """Response for queue position check"""
    queue_entry_id: UUID
    event_id: int
    position: int
    status: str
    estimated_wait_minutes: int | None = None
    total_ahead: int
    expires_at: datetime.datetime | None = None
    can_proceed: bool = False


class QueueStatusResponse(BaseSchemaModel):
    """Response for public queue status"""
    event_id: int
    queue_enabled: bool
    total_in_queue: int
    currently_processing: int
    estimated_wait_minutes: int | None = None
    is_queue_active: bool


class QueueLeaveResponse(BaseSchemaModel):
    """Response when leaving a queue"""
    success: bool
    message: str


# WebSocket message schemas
class QueueWebSocketMessage(BaseSchemaModel):
    """WebSocket message for queue updates"""
    type: str  # position_update, status_change, error, heartbeat
    data: dict


class QueuePositionUpdate(BaseSchemaModel):
    """Position update data sent via WebSocket"""
    position: int
    status: str
    estimated_wait_minutes: int | None = None
    total_ahead: int
    expires_at: datetime.datetime | None = None
    can_proceed: bool = False


class QueueStatusChange(BaseSchemaModel):
    """Status change notification sent via WebSocket"""
    old_status: str
    new_status: str
    message: str
    redirect_url: str | None = None
