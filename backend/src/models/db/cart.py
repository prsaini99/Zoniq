import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


class Cart(Base):
    """
    Shopping cart for a user's pending ticket selections.
    Each cart is scoped to a single event.
    Carts have an expiration time to automatically release locked seats.
    """
    __tablename__ = "cart"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Status
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="active"
    )  # active, converted, abandoned, expired
    # Cart expiry (auto-expire after inactivity)
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
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

    __table_args__ = (
        sqlalchemy.Index("ix_cart_user_event", "user_id", "event_id"),
        sqlalchemy.Index("ix_cart_status", "status"),
        sqlalchemy.Index("ix_cart_expires", "expires_at"),
    )

    # Relationships
    items = relationship("CartItem", back_populates="cart", lazy="selectin", cascade="all, delete-orphan")
    event = relationship("Event", lazy="joined")

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user={self.user_id}, event={self.event_id}, status='{self.status}')>"

    @property
    def is_expired(self) -> bool:
        """Check if cart has expired"""
        now = datetime.datetime.now(datetime.timezone.utc)
        return now > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if cart is still active"""
        return self.status == "active" and not self.is_expired


class CartItem(Base):
    """
    Individual item in a cart.
    Represents selected tickets for a seat category.
    """
    __tablename__ = "cart_item"

    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    cart_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("cart.id", ondelete="CASCADE"), nullable=False
    )
    seat_category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # For assigned seating — specific seat IDs stored as JSON array
    seat_ids: SQLAlchemyMapped[list | None] = sqlalchemy_mapped_column(
        sqlalchemy.JSON, nullable=True
    )
    # Quantity (for general admission without specific seats)
    quantity: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    # Price snapshot
    unit_price: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Seat lock expiry
    locked_until: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
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
        sqlalchemy.Index("ix_cart_item_cart", "cart_id"),
    )

    # Relationships
    cart = relationship("Cart", back_populates="items")
    seat_category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, category={self.seat_category_id}, qty={self.quantity})>"

    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return float(self.unit_price) * self.quantity
