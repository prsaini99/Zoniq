import datetime
from typing import Any
from decimal import Decimal

import pydantic

from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.venue import VenueCompact
from src.models.db.event import EventStatus, EventCategory


# ==================== Input Schemas ====================

class EventCreate(BaseSchemaModel):
    """Schema for creating a new event"""
    title: str = pydantic.Field(..., min_length=1, max_length=255)
    description: str | None = None
    short_description: str | None = pydantic.Field(None, max_length=500)
    category: str = pydantic.Field(default=EventCategory.OTHER.value)
    venue_id: int | None = None
    event_date: datetime.datetime
    event_end_date: datetime.datetime | None = None
    booking_start_date: datetime.datetime
    booking_end_date: datetime.datetime
    banner_image_url: str | None = pydantic.Field(None, max_length=500)
    thumbnail_image_url: str | None = pydantic.Field(None, max_length=500)
    terms_and_conditions: str | None = None
    organizer_name: str | None = pydantic.Field(None, max_length=255)
    organizer_contact: str | None = pydantic.Field(None, max_length=255)
    max_tickets_per_booking: int = pydantic.Field(default=10, ge=1, le=50)
    extra_data: dict[str, Any] | None = None
    # Queue settings
    queue_enabled: bool = pydantic.Field(default=False)
    queue_batch_size: int = pydantic.Field(default=50, ge=1, le=500)
    queue_processing_minutes: int = pydantic.Field(default=10, ge=1, le=60)

    @pydantic.model_validator(mode="after")
    def validate_dates(self):
        if self.booking_end_date <= self.booking_start_date:
            raise ValueError("booking_end_date must be after booking_start_date")
        if self.event_date < self.booking_start_date:
            raise ValueError("event_date should be after or on booking_start_date")
        if self.event_end_date and self.event_end_date < self.event_date:
            raise ValueError("event_end_date must be after event_date")
        return self


class EventUpdate(BaseSchemaModel):
    """Schema for updating an event"""
    title: str | None = pydantic.Field(None, min_length=1, max_length=255)
    description: str | None = None
    short_description: str | None = pydantic.Field(None, max_length=500)
    category: str | None = None
    venue_id: int | None = None
    event_date: datetime.datetime | None = None
    event_end_date: datetime.datetime | None = None
    booking_start_date: datetime.datetime | None = None
    booking_end_date: datetime.datetime | None = None
    banner_image_url: str | None = pydantic.Field(None, max_length=500)
    thumbnail_image_url: str | None = pydantic.Field(None, max_length=500)
    terms_and_conditions: str | None = None
    organizer_name: str | None = pydantic.Field(None, max_length=255)
    organizer_contact: str | None = pydantic.Field(None, max_length=255)
    max_tickets_per_booking: int | None = pydantic.Field(None, ge=1, le=50)
    extra_data: dict[str, Any] | None = None
    # Queue settings
    queue_enabled: bool | None = None
    queue_batch_size: int | None = pydantic.Field(None, ge=1, le=500)
    queue_processing_minutes: int | None = pydantic.Field(None, ge=1, le=60)


# ==================== Response Schemas ====================

class EventResponse(BaseSchemaModel):
    """Schema for event in responses (public)"""
    id: int
    title: str
    slug: str
    short_description: str | None = None
    category: str
    venue: VenueCompact | None = None
    event_date: datetime.datetime
    event_end_date: datetime.datetime | None = None
    booking_start_date: datetime.datetime
    booking_end_date: datetime.datetime
    status: str
    banner_image_url: str | None = None
    thumbnail_image_url: str | None = None
    organizer_name: str | None = None
    total_seats: int
    available_seats: int
    max_tickets_per_booking: int
    is_booking_open: bool = False
    created_at: datetime.datetime
    # Queue settings
    queue_enabled: bool = False
    queue_batch_size: int | None = None
    queue_processing_minutes: int | None = None


class EventDetailResponse(EventResponse):
    """Schema for detailed event response"""
    description: str | None = None
    terms_and_conditions: str | None = None
    organizer_contact: str | None = None
    extra_data: dict[str, Any] | None = None
    published_at: datetime.datetime | None = None


class EventAdminResponse(EventDetailResponse):
    """Schema for admin event response (includes all fields)"""
    created_by: int | None = None
    updated_at: datetime.datetime | None = None
    cancelled_at: datetime.datetime | None = None


class EventListResponse(BaseSchemaModel):
    """Schema for paginated event list"""
    events: list[EventResponse]
    total: int
    page: int
    page_size: int


# ==================== Seat Category Schemas ====================

class SeatCategoryCreate(BaseSchemaModel):
    """Schema for creating a seat category"""
    name: str = pydantic.Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: Decimal = pydantic.Field(..., ge=0)
    total_seats: int = pydantic.Field(..., ge=1)
    display_order: int = pydantic.Field(default=0)
    color_code: str | None = pydantic.Field(default="#3B82F6", max_length=10)


class SeatCategoryUpdate(BaseSchemaModel):
    """Schema for updating a seat category"""
    name: str | None = pydantic.Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = pydantic.Field(None, ge=0)
    total_seats: int | None = pydantic.Field(None, ge=1)
    display_order: int | None = None
    color_code: str | None = pydantic.Field(None, max_length=10)
    is_active: bool | None = None


class SeatCategoryResponse(BaseSchemaModel):
    """Schema for seat category in responses"""
    id: int
    event_id: int
    name: str
    description: str | None = None
    price: Decimal
    total_seats: int
    available_seats: int
    display_order: int
    color_code: str | None = None
    is_active: bool
    created_at: datetime.datetime


# ==================== Seat Schemas ====================

class SeatCreate(BaseSchemaModel):
    """Schema for creating a seat"""
    category_id: int
    seat_number: str | None = pydantic.Field(None, max_length=20)
    row_name: str | None = pydantic.Field(None, max_length=10)
    section: str | None = pydantic.Field(None, max_length=50)
    position_x: int | None = None
    position_y: int | None = None


class SeatBulkCreate(BaseSchemaModel):
    """Schema for bulk creating seats"""
    category_id: int
    section: str | None = None
    rows: list[str]  # ["A", "B", "C"]
    seats_per_row: int = pydantic.Field(..., ge=1, le=100)


class SeatUpdate(BaseSchemaModel):
    """Schema for updating a seat"""
    category_id: int | None = None
    seat_number: str | None = pydantic.Field(None, max_length=20)
    row_name: str | None = pydantic.Field(None, max_length=10)
    section: str | None = pydantic.Field(None, max_length=50)
    status: str | None = None  # Only admin can change to 'blocked'
    position_x: int | None = None
    position_y: int | None = None


class SeatResponse(BaseSchemaModel):
    """Schema for seat in responses"""
    id: int
    event_id: int
    category_id: int
    seat_number: str | None = None
    row_name: str | None = None
    section: str | None = None
    status: str
    seat_label: str | None = None
    position_x: int | None = None
    position_y: int | None = None


class SeatAvailabilityResponse(BaseSchemaModel):
    """Schema for seat availability (optimized for frontend)"""
    id: int
    category_id: int
    seat_label: str | None = None
    row_name: str | None = None
    section: str | None = None
    status: str  # available, locked, booked, blocked
    position_x: int | None = None
    position_y: int | None = None


class EventSeatsResponse(BaseSchemaModel):
    """Schema for event seats with categories"""
    event_id: int
    categories: list[SeatCategoryResponse]
    seats: list[SeatAvailabilityResponse]
    total_seats: int
    available_seats: int


# ==================== Filter/Search Schemas ====================

class EventSearchParams(BaseSchemaModel):
    """Schema for event search parameters"""
    query: str | None = None
    category: str | None = None
    city: str | None = None
    date_from: datetime.date | None = None
    date_to: datetime.date | None = None
    status: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
