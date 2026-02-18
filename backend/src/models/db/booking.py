import datetime
import uuid

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class Booking(Base):
    """
    A confirmed booking (order) for event tickets.
    Created when a user checks out from their cart.
    """
    __tablename__ = "booking"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Unique human-readable booking number (e.g., "ZNQ-20260212-A1B2C3")
    booking_number: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, unique=True
    )
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Status
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="confirmed"
    )  # pending, confirmed, cancelled, refunded
    # Pricing
    total_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    discount_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False, default=0
    )
    final_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Payment
    payment_status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="pending"
    )  # pending, success, failed, refunded
    payment_id: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Promo code used (historical record - feature removed)
    promo_code_used: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Ticket count
    ticket_count: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Contact info (snapshot at time of booking)
    contact_email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    contact_phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
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
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"eager_defaults": True}

    __table_args__ = (
        sqlalchemy.Index("ix_booking_user", "user_id"),
        sqlalchemy.Index("ix_booking_event", "event_id"),
        sqlalchemy.Index("ix_booking_status", "status"),
        sqlalchemy.Index("ix_booking_number", "booking_number"),
    )

    # Relationships
    items = relationship("BookingItem", back_populates="booking", lazy="selectin")
    event = relationship("Event", lazy="joined")
    user = relationship("Account", lazy="joined")

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, number='{self.booking_number}', status='{self.status}')>"

    @staticmethod
    def generate_booking_number() -> str:
        """Generate a unique booking number like ZNQ-20260212-A1B2C3"""
        date_part = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"ZNQ-{date_part}-{unique_part}"


class BookingItem(Base):
    """
    Individual ticket within a booking.
    Each item represents one seat/ticket.
    """
    __tablename__ = "booking_item"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    booking_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    seat_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat.id", ondelete="SET NULL"), nullable=True
    )
    category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # Price snapshot at time of booking
    price: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Category name snapshot
    category_name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False
    )
    # Seat label snapshot
    seat_label: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Ticket identification
    ticket_number: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, unique=True
    )
    # Usage tracking
    is_used: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    used_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Timestamps
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    __mapper_args__ = {"eager_defaults": True}

    __table_args__ = (
        sqlalchemy.Index("ix_booking_item_booking", "booking_id"),
        sqlalchemy.Index("ix_booking_item_ticket", "ticket_number"),
    )

    # Relationships
    booking = relationship("Booking", back_populates="items")
    category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        return f"<BookingItem(id={self.id}, ticket='{self.ticket_number}')>"

    @staticmethod
    def generate_ticket_number() -> str:
        """Generate a unique ticket number like TKT-A1B2C3D4"""
        unique_part = uuid.uuid4().hex[:8].upper()
        return f"TKT-{unique_part}"
