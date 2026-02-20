# Queue schemas for virtual waiting queue system used during high-demand event bookings
import datetime
from uuid import UUID

from src.models.schemas.base import BaseSchemaModel


# Schema for requesting to join the virtual queue (event_id is provided via URL path)
class QueueJoinRequest(BaseSchemaModel):
    """Request to join a queue - event_id comes from path parameter"""
    pass


# Response returned when a user successfully joins the queue
class QueueJoinResponse(BaseSchemaModel):
    """Response when joining a queue"""
    # Unique identifier for this queue entry
    queue_entry_id: UUID
    # The event this queue is for
    event_id: int
    # User's current position in the queue (1-based)
    position: int
    # Queue entry status (e.g., waiting, processing, expired)
    status: str
    # Estimated minutes until the user can start booking
    estimated_wait_minutes: int | None = None
    # Number of people ahead of this user in the queue
    total_ahead: int
    # When the user joined the queue
    joined_at: datetime.datetime


# Response for checking the user's current position in the queue
class QueuePositionResponse(BaseSchemaModel):
    """Response for queue position check"""
    queue_entry_id: UUID
    event_id: int
    position: int
    status: str
    estimated_wait_minutes: int | None = None
    total_ahead: int
    # When the user's booking window expires (only set when status is "processing")
    expires_at: datetime.datetime | None = None
    # Whether the user is allowed to proceed to booking
    can_proceed: bool = False


# Public-facing queue status for an event (no user-specific data)
class QueueStatusResponse(BaseSchemaModel):
    """Response for public queue status"""
    event_id: int
    # Whether the queue feature is enabled for this event
    queue_enabled: bool
    # Total number of users currently waiting in the queue
    total_in_queue: int
    # Number of users currently in their booking window
    currently_processing: int
    # Estimated wait time for a new joiner
    estimated_wait_minutes: int | None = None
    # Whether the queue is actively accepting new entries
    is_queue_active: bool


# Response when a user voluntarily leaves the queue
class QueueLeaveResponse(BaseSchemaModel):
    """Response when leaving a queue"""
    success: bool
    message: str


# WebSocket message schemas for real-time queue updates

# Generic WebSocket message wrapper sent to connected clients
class QueueWebSocketMessage(BaseSchemaModel):
    """WebSocket message for queue updates"""
    # Message type: position_update, status_change, error, or heartbeat
    type: str  # position_update, status_change, error, heartbeat
    # Payload containing the actual update data
    data: dict


# Position update payload sent via WebSocket when the user's queue position changes
class QueuePositionUpdate(BaseSchemaModel):
    """Position update data sent via WebSocket"""
    position: int
    status: str
    estimated_wait_minutes: int | None = None
    total_ahead: int
    expires_at: datetime.datetime | None = None
    can_proceed: bool = False


# Status change notification sent via WebSocket when the user's queue status transitions
class QueueStatusChange(BaseSchemaModel):
    """Status change notification sent via WebSocket"""
    old_status: str
    new_status: str
    # Human-readable message explaining the status change
    message: str
    # URL to redirect the user to (e.g., booking page when it's their turn)
    redirect_url: str | None = None
