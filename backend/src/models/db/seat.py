import datetime
from enum import Enum

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class SeatStatus(str, Enum):
    AVAILABLE = "available"
    LOCKED = "locked"      # Temporarily locked during checkout
    BOOKED = "booked"      # Successfully booked
    BLOCKED = "blocked"    # Blocked by admin (not for sale)


class Seat(Base):
    """
    Individual seats for an event.
    For general admission events, seats might not have specific numbers.
    For assigned seating, each seat has a unique identifier (row + number).
    """
    __tablename__ = "seat"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # Seat identification (for assigned seating)
    seat_number: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=20), nullable=True
    )
    row_name: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=10), nullable=True
    )
    section: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Status
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default=SeatStatus.AVAILABLE.value
    )
    # Lock mechanism (for seat reservation during checkout)
    locked_until: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    locked_by: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="SET NULL"), nullable=True
    )
    # Booking reference (set when successfully booked)
    booking_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True  # Will be FK to booking table
    )
    # Position for seat map rendering (optional)
    position_x: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    position_y: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    # Timestamps
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    # Indexes for performance
    __table_args__ = (
        sqlalchemy.Index("ix_seat_event_status", "event_id", "status"),
        sqlalchemy.Index("ix_seat_category", "category_id"),
        sqlalchemy.Index("ix_seat_locked_until", "locked_until"),
    )

    # Relationships
    category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        seat_label = self.seat_label or f"ID:{self.id}"
        return f"<Seat({seat_label}, status='{self.status}')>"

    @property
    def seat_label(self) -> str | None:
        """Get human-readable seat label"""
        if self.row_name and self.seat_number:
            if self.section:
                return f"{self.section}-{self.row_name}{self.seat_number}"
            return f"{self.row_name}{self.seat_number}"
        return self.seat_number

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

    @property
    def is_locked(self) -> bool:
        """Check if seat is currently locked"""
        if self.status != SeatStatus.LOCKED.value:
            return False
        if self.locked_until:
            now = datetime.datetime.now(datetime.timezone.utc)
            return now <= self.locked_until
        return False
