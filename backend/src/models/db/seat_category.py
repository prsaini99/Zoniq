import datetime
from decimal import Decimal

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class SeatCategory(Base):
    """
    Seat categories represent pricing tiers for an event.
    Examples: VIP, Premium, Standard, Economy, etc.
    """
    __tablename__ = "seat_category"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    name: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=100), nullable=False
    )
    description: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.Text, nullable=True
    )
    # Pricing
    price: SQLAlchemyMapped[Decimal] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Seat counts
    total_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    available_seats: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False
    )
    # Display order (lower = higher priority in UI)
    display_order: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=0
    )
    # Color for UI display (hex code)
    color_code: SQLAlchemyMapped[str | None] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=10), nullable=True, default="#3B82F6"
    )
    # Status
    is_active: SQLAlchemyMapped[bool] = sqlalchemy_mapped_column(
        sqlalchemy.Boolean, nullable=False, default=True
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

    # Unique constraint: one category name per event
    __table_args__ = (
        sqlalchemy.UniqueConstraint("event_id", "name", name="uq_event_category_name"),
    )

    def __repr__(self) -> str:
        return f"<SeatCategory(id={self.id}, name='{self.name}', price={self.price})>"

    @property
    def is_available(self) -> bool:
        """Check if this category has available seats"""
        return self.is_active and self.available_seats > 0

    @property
    def sold_seats(self) -> int:
        """Get number of sold seats"""
        return self.total_seats - self.available_seats
