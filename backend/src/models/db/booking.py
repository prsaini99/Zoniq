# Booking and BookingItem models -- represent confirmed ticket orders and individual tickets
import datetime
import uuid

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Database model for a confirmed booking (order) of event tickets
# Created when a user successfully checks out from their cart
class Booking(Base):
    """
    A confirmed booking (order) for event tickets.
    Created when a user checks out from their cart.
    """
    __tablename__ = "booking"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Unique human-readable booking number (e.g., "ZNQ-20260212-A1B2C3")
    # Used for customer-facing references and lookups
    booking_number: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, unique=True
    )
    # Foreign key to the user who made the booking; cascades on user deletion
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the event being booked; cascades on event deletion
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Status
    # Lifecycle status of the booking: pending, confirmed, cancelled, or refunded
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="confirmed"
    )  # pending, confirmed, cancelled, refunded
    # Pricing
    # Gross total before any discounts
    total_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Amount discounted (e.g., via promo code), defaults to 0
    discount_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False, default=0
    )
    # Net amount charged to the user after discounts (total_amount - discount_amount)
    final_amount: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Payment
    # Status of the payment: pending, success, failed, or refunded
    payment_status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="pending"
    )  # pending, success, failed, refunded
    # External payment gateway transaction ID (e.g., Razorpay payment ID)
    payment_id: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Promo code used (historical record - feature removed)
    # Stored as a snapshot for audit purposes even though promo codes may no longer be active
    promo_code_used: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Ticket count
    # Total number of individual tickets in this booking
    ticket_count: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Contact info (snapshot at time of booking)
    # Email captured at booking time, used for sending tickets and notifications
    contact_email: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=255), nullable=True
    )
    # Phone number captured at booking time
    contact_phone: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Timestamps
    # When the booking was created
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the booking was last updated
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # When the booking was cancelled, if applicable
    cancelled_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Indexes for commonly queried columns to improve lookup performance
    __table_args__ = (
        sqlalchemy.Index("ix_booking_user", "user_id"),
        sqlalchemy.Index("ix_booking_event", "event_id"),
        sqlalchemy.Index("ix_booking_status", "status"),
        sqlalchemy.Index("ix_booking_number", "booking_number"),
    )

    # Relationships
    # One-to-many: a booking contains multiple booking items (tickets); eagerly loaded via SELECT IN
    items = relationship("BookingItem", back_populates="booking", lazy="selectin")
    # Many-to-one: each booking references one event; eager-loaded via JOIN
    event = relationship("Event", lazy="joined")
    # Many-to-one: each booking belongs to one user; eager-loaded via JOIN
    user = relationship("Account", lazy="joined")

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, number='{self.booking_number}', status='{self.status}')>"

    # Generates a unique, human-readable booking number with date and random suffix
    # Format: ZNQ-YYYYMMDD-XXXXXX (e.g., "ZNQ-20260212-A1B2C3")
    @staticmethod
    def generate_booking_number() -> str:
        """Generate a unique booking number like ZNQ-20260212-A1B2C3"""
        date_part = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"ZNQ-{date_part}-{unique_part}"


# Database model for an individual ticket within a booking
# Each BookingItem represents one seat/ticket with its price snapshot and usage tracking
class BookingItem(Base):
    """
    Individual ticket within a booking.
    Each item represents one seat/ticket.
    """
    __tablename__ = "booking_item"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the parent booking; cascades on booking deletion
    booking_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("booking.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the specific seat; set NULL if the seat record is deleted
    seat_id: SQLAlchemyMapped[int | None] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat.id", ondelete="SET NULL"), nullable=True
    )
    # Foreign key to the seat category (pricing tier); cascades on category deletion
    category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # Price snapshot at time of booking
    # Captures the price at checkout so later price changes do not affect existing bookings
    price: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Category name snapshot
    # Stored so the category name is preserved even if the category is later renamed
    category_name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False
    )
    # Seat label snapshot
    # Human-readable seat label (e.g., "A12") preserved for ticket display
    seat_label: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=True
    )
    # Ticket identification
    # Unique ticket number used for entry validation (e.g., "TKT-A1B2C3D4")
    ticket_number: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, unique=True
    )
    # Usage tracking
    # Whether this ticket has been scanned/used for entry
    is_used: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=False
    )
    # Timestamp when the ticket was scanned/used at the venue
    used_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Timestamps
    # When the booking item was created
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Indexes for looking up items by booking and by ticket number
    __table_args__ = (
        sqlalchemy.Index("ix_booking_item_booking", "booking_id"),
        sqlalchemy.Index("ix_booking_item_ticket", "ticket_number"),
    )

    # Relationships
    # Many-to-one: each booking item belongs to one booking
    booking = relationship("Booking", back_populates="items")
    # Many-to-one: each booking item references one seat category; eager-loaded via JOIN
    category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        return f"<BookingItem(id={self.id}, ticket='{self.ticket_number}')>"

    # Generates a unique ticket number with the "TKT-" prefix and 8-character hex suffix
    @staticmethod
    def generate_ticket_number() -> str:
        """Generate a unique ticket number like TKT-A1B2C3D4"""
        unique_part = uuid.uuid4().hex[:8].upper()
        return f"TKT-{unique_part}"
