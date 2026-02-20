# Seat model -- represents an individual seat for an event, supporting both assigned and general admission seating
import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Enum representing the possible states of a seat throughout its lifecycle
class SeatStatus(str, Enum):
    AVAILABLE = "available"
    LOCKED = "locked"      # Temporarily locked during checkout
    BOOKED = "booked"      # Successfully booked
    BLOCKED = "blocked"    # Blocked by admin (not for sale)


# Database model for individual seats within an event
# For general admission: seats may lack specific numbers
# For assigned seating: each seat has a unique identifier (section + row + number)
class Seat(Base):
    """
    Individual seats for an event.
    For general admission events, seats might not have specific numbers.
    For assigned seating, each seat has a unique identifier (row + number).
    """
    __tablename__ = "seat"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the event this seat belongs to; cascades on event deletion
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the seat category (pricing tier) this seat belongs to
    category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # Seat identification (for assigned seating)
    # Individual seat number within a row (e.g., "12", "A1")
    seat_number: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    # Row identifier (e.g., "A", "B", "AA")
    row_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=10), nullable=True
    )
    # Section or zone of the venue (e.g., "North Stand", "Mezzanine")
    section: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Status
    # Current status of the seat (available, locked, booked, or blocked)
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=SeatStatus.AVAILABLE.value
    )
    # Lock mechanism (for seat reservation during checkout)
    # Timestamp when the temporary lock expires; after this time the seat is released
    locked_until: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Foreign key to the user who has locked this seat during checkout
    locked_by: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Booking reference (set when successfully booked)
    # ID of the booking that owns this seat; populated after successful payment
    booking_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True  # Will be FK to booking table
    )
    # Position for seat map rendering (optional)
    # X coordinate for rendering this seat on a visual seat map
    position_x: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    # Y coordinate for rendering this seat on a visual seat map
    position_y: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    # Timestamps
    # When the seat record was created in the database
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the seat record was last updated
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Indexes for performance
    # Composite index on event_id + status for filtering available seats per event
    # Index on category_id for filtering seats by pricing tier
    # Index on locked_until for efficiently finding and releasing expired locks
    __table_args__ = (
        sqlalchemy.Index("ix_seat_event_status", "event_id", "status"),
        sqlalchemy.Index("ix_seat_category", "category_id"),
        sqlalchemy.Index("ix_seat_locked_until", "locked_until"),
    )

    # Relationships
    # Many-to-one: each seat belongs to one seat category; eager-loaded via JOIN
    category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        seat_label = self.seat_label or f"ID:{self.id}"
        return f"<Seat({seat_label}, status='{self.status}')>"

    # Builds a human-readable seat label from section, row, and seat number
    @property
    def seat_label(self) -> str | None:
        """Get human-readable seat label"""
        if self.row_name and self.seat_number:
            if self.section:
                return f"{self.section}-{self.row_name}{self.seat_number}"
            return f"{self.row_name}{self.seat_number}"
        return self.seat_number

    # Returns True if the seat can be booked; also considers expired locks as available
    @property
    def is_available(self) -> bool:
        """Check if seat is available for booking"""
        if self.status != SeatStatus.AVAILABLE.value:
            # Check if lock has expired
            if self.status == SeatStatus.LOCKED.value and self.locked_until:
                now = datetime.datetime.now(datetime.timezone.utc)
                if now > self.locked_until:
                    return True  # Lock expired
            return False
        return True

    # Returns True if the seat is locked and the lock has not yet expired
    @property
    def is_locked(self) -> bool:
        """Check if seat is currently locked"""
        if self.status != SeatStatus.LOCKED.value:
            return False
        if self.locked_until:
            now = datetime.datetime.now(datetime.timezone.utc)
            return now <= self.locked_until
        return False
