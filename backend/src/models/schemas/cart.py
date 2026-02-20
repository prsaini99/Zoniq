# Cart schemas for managing shopping carts, cart items, and checkout in the ticket booking flow
import datetime
from decimal import Decimal

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

# Schema for creating or retrieving a cart for a specific event
class CartCreate(BaseSchemaModel):
    """Schema for creating/getting a cart"""
    # The event this cart is associated with
    event_id: int


# Schema for adding a ticket item to the cart
class CartAddItem(BaseSchemaModel):
    """Schema for adding an item to cart"""
    # The event the ticket is for
    event_id: int
    # The seat category being purchased (e.g., VIP, General)
    seat_category_id: int
    # Number of tickets to add (1-10 per item)
    quantity: int = pydantic.Field(default=1, ge=1, le=10)
    # Optional list of specific seat IDs for assigned/reserved seating
    seat_ids: list[int] | None = None  # For assigned seating


# Schema for updating the quantity of an existing cart item
class CartUpdateItem(BaseSchemaModel):
    """Schema for updating cart item quantity"""
    # New quantity for the cart item (1-10)
    quantity: int = pydantic.Field(ge=1, le=10)


# Schema for initiating checkout, with optional contact details for the booking
class CheckoutRequest(BaseSchemaModel):
    """Schema for checkout"""
    # Email to send booking confirmation to (defaults to account email if not provided)
    contact_email: str | None = None
    # Phone number for booking-related communication
    contact_phone: str | None = None


# ==================== Response Schemas ====================

# Schema representing a single item in the cart
class CartItemResponse(BaseSchemaModel):
    """Schema for cart item in responses"""
    id: int
    # The seat category ID for this line item
    seat_category_id: int
    # Display name of the seat category (e.g., "VIP")
    category_name: str | None = None
    # Color code of the category for UI display
    category_color: str | None = None
    # Specific seat IDs if assigned seating is used
    seat_ids: list[int] | None = None
    # Number of tickets in this line item
    quantity: int
    # Price per ticket
    unit_price: Decimal
    # Computed total for this line item (unit_price * quantity)
    subtotal: Decimal
    # Timestamp until which the selected seats are temporarily locked for this user
    locked_until: datetime.datetime | None = None


# Schema representing the full cart with all items and pricing summary
class CartResponse(BaseSchemaModel):
    """Schema for cart in responses"""
    id: int
    # The user who owns this cart
    user_id: int
    # The event this cart is for
    event_id: int
    # Event details for display purposes
    event_title: str | None = None
    event_date: datetime.datetime | None = None
    event_image: str | None = None
    # Cart status (e.g., active, checked_out, expired)
    status: str
    # List of all items in the cart
    items: list[CartItemResponse] = []
    # Sum of all item subtotals before any discounts
    subtotal: Decimal
    # Final amount after applying discounts or promo codes
    total: Decimal
    # Total number of tickets across all items
    item_count: int
    # When the cart and its seat locks expire (carts are time-limited)
    expires_at: datetime.datetime


# Schema for the result of validating a cart before checkout
class CartValidationResponse(BaseSchemaModel):
    """Schema for cart validation result"""
    # Whether the cart is valid and ready for checkout
    is_valid: bool
    # Blocking errors that prevent checkout (e.g., seats no longer available)
    errors: list[str] = []
    # Non-blocking warnings (e.g., event date approaching soon)
    warnings: list[str] = []
