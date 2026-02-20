# SeatCategory model -- represents a pricing tier / ticket type for an event (e.g., VIP, Premium, Standard)
import datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Database model for seat categories, defining ticket pricing tiers per event
# Examples: VIP, Premium, Standard, Economy, etc.
class SeatCategory(Base):
    """
    Seat categories represent pricing tiers for an event.
    Examples: VIP, Premium, Standard, Economy, etc.
    """
    __tablename__ = "seat_category"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the event this category belongs to; cascades on event deletion
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Name of the category (e.g., "VIP", "Standard", "Balcony")
    name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False
    )
    # Optional description providing details about the category (e.g., perks, view quality)
    description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # Pricing
    # Ticket price for this category, stored with 2 decimal places
    price: SQLAlchemyMapped[Decimal] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Seat counts
    # Total number of seats allocated to this category
    total_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    # Number of seats still available; decremented as bookings are made
    available_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    # Display order (lower = higher priority in UI)
    # Controls the sort order when rendering categories on the frontend
    display_order: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Color for UI display (hex code)
    # Hex color code used to visually distinguish this category in the seat map UI
    color_code: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=10), nullable=True, default="#3B82F6"
    )
    # Status
    # Whether this category is currently active and available for sale
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
    )
    # Timestamps
    # When the category record was created in the database
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the category record was last updated
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Unique constraint: one category name per event
    # Prevents duplicate category names within the same event
    __table_args__ = (
        sqlalchemy.UniqueConstraint("event_id", "name", name="uq_event_category_name"),
    )

    def __repr__(self) -> str:
        return f"<SeatCategory(id={self.id}, name='{self.name}', price={self.price})>"

    # Returns True if the category is active and has remaining seats
    @property
    def is_available(self) -> bool:
        """Check if this category has available seats"""
        return self.is_active and self.available_seats > 0

    # Calculates the number of seats that have been sold (total minus available)
    @property
    def sold_seats(self) -> int:
        """Get number of sold seats"""
        return self.total_seats - self.available_seats
