# Booking schemas for managing ticket bookings, booking items, and booking responses
import datetime
from decimal import Decimal
from typing import Any

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

# Schema for cancelling an existing booking
class BookingCancel(BaseSchemaModel):
    """Schema for cancelling a booking"""
    # Optional reason for the cancellation (for record-keeping)
    reason: str | None = None


# ==================== Response Schemas ====================

# Schema for a single line item within a booking (one per ticket)
class BookingItemResponse(BaseSchemaModel):
    """Schema for booking item in responses"""
    id: int
    # The booking this item belongs to
    booking_id: int
    # Specific seat assigned to this ticket (None for general admission)
    seat_id: int | None = None
    # Seat category this ticket belongs to
    category_id: int
    # Display name of the seat category
    category_name: str
    # Human-readable seat label (e.g., "A-12")
    seat_label: str | None = None
    # Price paid for this specific ticket
    price: Decimal
    # Unique ticket identifier for entry validation
    ticket_number: str
    # Whether this ticket has been scanned/used at the event
    is_used: bool
    # When the ticket was marked as used
    used_at: datetime.datetime | None = None


# Compact event information embedded in booking responses for display purposes
class BookingEventInfo(BaseSchemaModel):
    """Compact event info embedded in booking response"""
    id: int
    title: str
    slug: str
    event_date: datetime.datetime
    banner_image_url: str | None = None
    thumbnail_image_url: str | None = None
    # Venue details for display in the booking summary
    venue_name: str | None = None
    venue_city: str | None = None


# Standard booking response with summary information
class BookingResponse(BaseSchemaModel):
    """Schema for booking in responses"""
    id: int
    # Unique human-readable booking reference number
    booking_number: str
    # The user who made this booking
    user_id: int
    # The event this booking is for
    event_id: int
    # Nested event details for display
    event: BookingEventInfo | None = None
    # Booking status (e.g., pending, confirmed, cancelled)
    status: str
    # Total price before any discounts
    total_amount: Decimal
    # Discount amount applied (from promo codes etc.)
    discount_amount: Decimal
    # Final amount charged (total_amount - discount_amount)
    final_amount: Decimal
    # Payment status (e.g., pending, paid, refunded)
    payment_status: str
    # Promo/coupon code applied to this booking (if any)
    promo_code_used: str | None = None
    # Total number of tickets in this booking
    ticket_count: int
    # Contact details provided during checkout
    contact_email: str | None = None
    contact_phone: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None


# Extended booking response that includes individual ticket/item details
class BookingDetailResponse(BookingResponse):
    """Schema for detailed booking response with items"""
    # List of individual booking items (one per ticket)
    items: list[BookingItemResponse] = []


# Paginated list of bookings
class BookingListResponse(BaseSchemaModel):
    """Schema for paginated booking list"""
    bookings: list[BookingResponse]
    total: int
    page: int
    page_size: int
