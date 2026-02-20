# Cart and CartItem models -- represent a user's shopping cart for pending ticket selections
import datetime

import sqlalchemy
from sqlalchemy.orm import Mapped as SQLAlchemyMapped, mapped_column as sqlalchemy_mapped_column, relationship

from src.repository.table import Base


# Database model for a shopping cart scoped to a single user and event
# Carts have an expiration time to automatically release locked seats if abandoned
class Cart(Base):
    """
    Shopping cart for a user's pending ticket selections.
    Each cart is scoped to a single event.
    Carts have an expiration time to automatically release locked seats.
    """
    __tablename__ = "cart"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the user who owns this cart; cascades on user deletion
    user_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the event this cart is associated with; one cart per event per user
    event_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    # Status
    # Current state of the cart: active, converted (to booking), abandoned, or expired
    status: SQLAlchemyMapped[str] = sqlalchemy_mapped_column(
        sqlalchemy.String(length=50), nullable=False, default="active"
    )  # active, converted, abandoned, expired
    # Cart expiry (auto-expire after inactivity)
    # Deadline after which the cart and its locked seats are automatically released
    expires_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=False
    )
    # Timestamps
    # When the cart was created
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )
    # When the cart was last modified
    updated_at: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Composite index for quickly finding a user's cart for a specific event
    # Index on status for filtering active/expired carts
    # Index on expires_at for background jobs that clean up expired carts
    __table_args__ = (
        sqlalchemy.Index("ix_cart_user_event", "user_id", "event_id"),
        sqlalchemy.Index("ix_cart_status", "status"),
        sqlalchemy.Index("ix_cart_expires", "expires_at"),
    )

    # Relationships
    # One-to-many: a cart contains multiple cart items; eagerly loaded via SELECT IN
    # Deleting a cart cascades to remove all its items
    items = relationship("CartItem", back_populates="cart", lazy="selectin", cascade="all, delete-orphan")
    # Many-to-one: each cart references one event; eager-loaded via JOIN
    event = relationship("Event", lazy="joined")

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user={self.user_id}, event={self.event_id}, status='{self.status}')>"

    # Returns True if the current UTC time is past the cart's expiration time
    @property
    def is_expired(self) -> bool:
        """Check if cart has expired"""
        now = datetime.datetime.now(datetime.timezone.utc)
        return now > self.expires_at

    # Returns True if the cart status is "active" and it has not yet expired
    @property
    def is_active(self) -> bool:
        """Check if cart is still active"""
        return self.status == "active" and not self.is_expired


# Database model for individual items within a cart
# Each item represents a selection of tickets for a specific seat category
class CartItem(Base):
    """
    Individual item in a cart.
    Represents selected tickets for a seat category.
    """
    __tablename__ = "cart_item"

    # Primary key, auto-incrementing integer
    id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        primary_key=True, autoincrement=True
    )
    # Foreign key to the parent cart; cascades on cart deletion
    cart_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("cart.id", ondelete="CASCADE"), nullable=False
    )
    # Foreign key to the seat category (pricing tier) for this item
    seat_category_id: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.ForeignKey("seat_category.id", ondelete="CASCADE"), nullable=False
    )
    # For assigned seating -- specific seat IDs stored as JSON array
    # Null for general admission where individual seats are not selected
    seat_ids: SQLAlchemyMapped[list | None] = sqlalchemy_mapped_column(
        sqlalchemy.JSON, nullable=True
    )
    # Quantity (for general admission without specific seats)
    # Number of tickets selected for this category
    quantity: SQLAlchemyMapped[int] = sqlalchemy_mapped_column(
        sqlalchemy.Integer, nullable=False, default=1
    )
    # Price snapshot
    # Unit price captured at the time the item was added to the cart (guards against price changes)
    unit_price: SQLAlchemyMapped[float] = sqlalchemy_mapped_column(
        sqlalchemy.Numeric(precision=10, scale=2), nullable=False
    )
    # Seat lock expiry
    # Timestamp until which the selected seats are locked for this cart item
    locked_until: SQLAlchemyMapped[datetime.datetime | None] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True), nullable=True
    )
    # Timestamps
    # When the cart item was added
    created_at: SQLAlchemyMapped[datetime.datetime] = sqlalchemy_mapped_column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    )

    # Eagerly load server-generated defaults after insert/update
    __mapper_args__ = {"eager_defaults": True}

    # Index on cart_id for efficiently retrieving all items belonging to a cart
    __table_args__ = (
        sqlalchemy.Index("ix_cart_item_cart", "cart_id"),
    )

    # Relationships
    # Many-to-one: each cart item belongs to one cart
    cart = relationship("Cart", back_populates="items")
    # Many-to-one: each cart item references one seat category; eager-loaded via JOIN
    seat_category = relationship("SeatCategory", lazy="joined")

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, category={self.seat_category_id}, qty={self.quantity})>"

    # Calculates the total price for this cart item (unit_price * quantity)
    @property
    def subtotal(self) -> float:
        """Calculate subtotal for this item"""
        return float(self.unit_price) * self.quantity
