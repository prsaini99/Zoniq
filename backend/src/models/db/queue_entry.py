# QueueEntry model -- manages virtual queue positions for high-demand events
import datetime
import uuid
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.repository.table import Base


# Enum representing the lifecycle states of a queue entry
class QueueStatus(str, Enum):
    WAITING = "waiting"        # User is in queue waiting
    PROCESSING = "processing"  # User's turn, can proceed to checkout
    COMPLETED = "completed"    # User completed checkout
    EXPIRED = "expired"        # User's turn expired (didn't checkout in time)
    LEFT = "left"              # User voluntarily left queue


# Database model for queue entries, used when an event has queue_enabled=True
# Users join the queue and are processed in batches based on their position
class QueueEntry(Base):
    """
    Queue entry for high-demand events.
    Manages virtual queue positions for users waiting to book tickets.
    """
    __tablename__ = "queue_entry"

    # Primary key using UUID for unpredictable, non-sequential identifiers
    id: SQLAlchemyMapped[uuid.UUID] = sqlalchemy_mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Foreign key to the event with the active queue; cascades on event deletion
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the user in the queue; cascades on user deletion
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # Numeric position in the queue; lower numbers are processed first
    position: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    # Current status of this queue entry (waiting, processing, completed, expired, left)
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=QueueStatus.WAITING.value
    )
    # Timestamps
    # When the user joined the queue
    joined_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the user's turn started (moved from waiting to processing)
    processed_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Deadline by which the user must complete checkout; after this, the entry expires
    expires_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # When the user successfully completed their booking from the queue
    completed_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Client info (for fraud detection)
    # IP address of the user when they joined the queue
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=45), nullable=True
    )
    # Browser user-agent string for identifying the client device
    user_agent: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Composite indexes for efficient queue operations:
    # - event + status: find all waiting/processing entries for an event
    # - event + position: determine queue order within an event
    # - user + event: check if a user is already in the queue for an event
    __table_args__ = (
        sqlalchemy.Index("ix_queue_entry_event_status", "event_id", "status"),
        sqlalchemy.Index("ix_queue_entry_event_position", "event_id", "position"),
        sqlalchemy.Index("ix_queue_entry_user_event", "user_id", "event_id"),
    )

    # Relationships - use "select" lazy loading to avoid FOR UPDATE conflicts
    # in scenarios where queue entries are locked for update during batch processing
    event = relationship("Event", lazy="select")
    user = relationship("Account", lazy="select")

    def __repr__(self) -> str:
        return f"<QueueEntry(id={self.id}, event={self.event_id}, user={self.user_id}, pos={self.position}, status='{self.status}')>"

    # Returns True if the user is still waiting or currently processing (not completed/expired/left)
    @property
    def is_active(self) -> bool:
        """Check if this queue entry is still active"""
        return self.status in [QueueStatus.WAITING.value, QueueStatus.PROCESSING.value]

    # Returns True if the processing window has passed (user took too long to check out)
    @property
    def is_expired(self) -> bool:
        """Check if the processing window has expired"""
        if not self.expires_at:
            return False
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    # Returns True if the user is in the "processing" state and their window has not expired
    @property
    def can_proceed(self) -> bool:
        """Check if user can proceed to checkout"""
        return self.status == QueueStatus.PROCESSING.value and not self.is_expired
