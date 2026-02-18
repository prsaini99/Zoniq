import datetime
from decimal import Decimal
from typing import Any

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

class BookingCancel(BaseSchemaModel):
    """Schema for cancelling a booking"""
    reason: str | None = None


# ==================== Response Schemas ====================

class BookingItemResponse(BaseSchemaModel):
    """Schema for booking item in responses"""
    id: int
    booking_id: int
    seat_id: int | None = None
    category_id: int
    category_name: str
    seat_label: str | None = None
    price: Decimal
    ticket_number: str
    is_used: bool
    used_at: datetime.datetime | None = None


class BookingEventInfo(BaseSchemaModel):
    """Compact event info embedded in booking response"""
    id: int
    title: str
    slug: str
    event_date: datetime.datetime
    banner_image_url: str | None = None
    thumbnail_image_url: str | None = None
    venue_name: str | None = None
    venue_city: str | None = None


class BookingResponse(BaseSchemaModel):
    """Schema for booking in responses"""
    id: int
    booking_number: str
    user_id: int
    event_id: int
    event: BookingEventInfo | None = None
    status: str
    total_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    payment_status: str
    promo_code_used: str | None = None
    ticket_count: int
    contact_email: str | None = None
    contact_phone: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None


class BookingDetailResponse(BookingResponse):
    """Schema for detailed booking response with items"""
    items: list[BookingItemResponse] = []


class BookingListResponse(BaseSchemaModel):
    """Schema for paginated booking list"""
    bookings: list[BookingResponse]
    total: int
    page: int
    page_size: int
