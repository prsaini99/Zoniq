import datetime
import uuid
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.repository.table import Base


class QueueStatus(str, Enum):
    WAITING = "waiting"        # User is in queue waiting
    PROCESSING = "processing"  # User's turn, can proceed to checkout
    COMPLETED = "completed"    # User completed checkout
    EXPIRED = "expired"        # User's turn expired (didn't checkout in time)
    LEFT = "left"              # User voluntarily left queue


class QueueEntry(Base):
    """
    Queue entry for high-demand events.
    Manages virtual queue positions for users waiting to book tickets.
    """
    __tablename__ = "queue_entry"

    id: SQLAlchemyMapped[uuid.UUID] = sqlalchemy_mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    position: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=QueueStatus.WAITING.value
    )
    # Timestamps
    joined_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    processed_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    expires_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    completed_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Client info (for fraud detection)
    ip_address: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=45), nullable=True
    )
    user_agent: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    __table_args__ = (
        sqlalchemy.Index("ix_queue_entry_event_status", "event_id", "status"),
        sqlalchemy.Index("ix_queue_entry_event_position", "event_id", "position"),
        sqlalchemy.Index("ix_queue_entry_user_event", "user_id", "event_id"),
    )

    # Relationships - use "select" lazy loading to avoid FOR UPDATE conflicts
    event = relationship("Event", lazy="select")
    user = relationship("Account", lazy="select")

    def __repr__(self) -> str:
        return f"<QueueEntry(id={self.id}, event={self.event_id}, user={self.user_id}, pos={self.position}, status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if this queue entry is still active"""
        return self.status in [QueueStatus.WAITING.value, QueueStatus.PROCESSING.value]

    @property
    def is_expired(self) -> bool:
        """Check if the processing window has expired"""
        if not self.expires_at:
            return False
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_at

    @property
    def can_proceed(self) -> bool:
        """Check if user can proceed to checkout"""
        return self.status == QueueStatus.PROCESSING.value and not self.is_expired
