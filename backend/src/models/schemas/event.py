# Event schemas for creating, updating, searching events, and managing seats and seat categories
import datetime
from typing import Any
from decimal import Decimal

import pydantic

from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.venue import VenueCompact
from src.models.db.event import EventStatus, EventCategory


# ==================== Input Schemas ====================

# Schema for creating a new event with all required and optional fields
class EventCreate(BaseSchemaModel):
    """Schema for creating a new event"""
    # Event title, required, between 1-255 characters
    title: str = pydantic.Field(..., min_length=1, max_length=255)
    # Full description of the event (rich text content)
    description: str | None = None
    # Brief summary shown in event listings, max 500 characters
    short_description: str | None = pydantic.Field(None, max_length=500)
    # Event category (defaults to OTHER if not specified)
    category: str = pydantic.Field(default=EventCategory.OTHER.value)
    # Optional foreign key linking the event to a venue
    venue_id: int | None = None
    # When the event starts
    event_date: datetime.datetime
    # When the event ends (optional for single-session events)
    event_end_date: datetime.datetime | None = None
    # Window during which ticket booking is allowed
    booking_start_date: datetime.datetime
    booking_end_date: datetime.datetime
    # URLs for promotional images
    banner_image_url: str | None = pydantic.Field(None, max_length=500)
    thumbnail_image_url: str | None = pydantic.Field(None, max_length=500)
    # Legal terms users must accept before booking
    terms_and_conditions: str | None = None
    # Contact details of the event organizer
    organizer_name: str | None = pydantic.Field(None, max_length=255)
    organizer_contact: str | None = pydantic.Field(None, max_length=255)
    # Maximum number of tickets a single user can book at once (1-50)
    max_tickets_per_booking: int = pydantic.Field(default=10, ge=1, le=50)
    # Flexible JSON field for storing additional event-specific metadata
    extra_data: dict[str, Any] | None = None
    # Queue settings for high-demand events
    # Whether to enable a virtual waiting queue for this event
    queue_enabled: bool = pydantic.Field(default=False)
    # Number of users processed per batch from the queue (1-500)
    queue_batch_size: int = pydantic.Field(default=50, ge=1, le=500)
    # Minutes each batch has to complete their booking (1-60)
    queue_processing_minutes: int = pydantic.Field(default=10, ge=1, le=60)

    # Validates that all date fields are logically consistent
    @pydantic.model_validator(mode="after")
    def validate_dates(self):
        if self.booking_end_date <= self.booking_start_date:
            raise ValueError("booking_end_date must be after booking_start_date")
        if self.event_date < self.booking_start_date:
            raise ValueError("event_date should be after or on booking_start_date")
        if self.event_end_date and self.event_end_date < self.event_date:
            raise ValueError("event_end_date must be after event_date")
        return self


# Schema for partially updating an event (all fields optional)
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

# Public-facing event response with summary information for event listings
class EventResponse(BaseSchemaModel):
    """Schema for event in responses (public)"""
    id: int
    title: str
    # URL-friendly identifier generated from the event title
    slug: str
    short_description: str | None = None
    category: str
    # Compact venue info (id, name, city, state) embedded in the response
    venue: VenueCompact | None = None
    event_date: datetime.datetime
    event_end_date: datetime.datetime | None = None
    booking_start_date: datetime.datetime
    booking_end_date: datetime.datetime
    # Current event status (e.g., draft, published, cancelled)
    status: str
    banner_image_url: str | None = None
    thumbnail_image_url: str | None = None
    organizer_name: str | None = None
    # Total number of seats across all categories
    total_seats: int
    # Number of seats still available for booking
    available_seats: int
    max_tickets_per_booking: int
    # Computed flag indicating whether booking is currently open
    is_booking_open: bool = False
    created_at: datetime.datetime
    # Queue settings
    queue_enabled: bool = False
    queue_batch_size: int | None = None
    queue_processing_minutes: int | None = None


# Extended event response including full description and organizer contact
class EventDetailResponse(EventResponse):
    """Schema for detailed event response"""
    description: str | None = None
    terms_and_conditions: str | None = None
    organizer_contact: str | None = None
    extra_data: dict[str, Any] | None = None
    # When the event was published (made visible to public)
    published_at: datetime.datetime | None = None


# Admin-only event response that includes internal tracking fields
class EventAdminResponse(EventDetailResponse):
    """Schema for admin event response (includes all fields)"""
    # ID of the admin who created this event
    created_by: int | None = None
    updated_at: datetime.datetime | None = None
    # When the event was cancelled (if applicable)
    cancelled_at: datetime.datetime | None = None


# Paginated list of events for listing endpoints
class EventListResponse(BaseSchemaModel):
    """Schema for paginated event list"""
    events: list[EventResponse]
    total: int
    page: int
    page_size: int


# ==================== Seat Category Schemas ====================

# Schema for creating a seat category (e.g., VIP, General, Balcony)
class SeatCategoryCreate(BaseSchemaModel):
    """Schema for creating a seat category"""
    # Display name of the category (e.g., "VIP", "General Admission")
    name: str = pydantic.Field(..., min_length=1, max_length=100)
    description: str | None = None
    # Ticket price for this category (must be non-negative)
    price: Decimal = pydantic.Field(..., ge=0)
    # Total number of seats available in this category (at least 1)
    total_seats: int = pydantic.Field(..., ge=1)
    # Order in which the category appears in the UI
    display_order: int = pydantic.Field(default=0)
    # Hex color code for visual identification in the seat map
    color_code: str | None = pydantic.Field(default="#3B82F6", max_length=10)


# Schema for partially updating a seat category
class SeatCategoryUpdate(BaseSchemaModel):
    """Schema for updating a seat category"""
    name: str | None = pydantic.Field(None, min_length=1, max_length=100)
    description: str | None = None
    price: Decimal | None = pydantic.Field(None, ge=0)
    total_seats: int | None = pydantic.Field(None, ge=1)
    display_order: int | None = None
    color_code: str | None = pydantic.Field(None, max_length=10)
    # Whether this category is active and available for booking
    is_active: bool | None = None


# Response schema for a seat category including computed availability
class SeatCategoryResponse(BaseSchemaModel):
    """Schema for seat category in responses"""
    id: int
    event_id: int
    name: str
    description: str | None = None
    price: Decimal
    total_seats: int
    # Dynamically computed: seats not yet booked or locked
    available_seats: int
    display_order: int
    color_code: str | None = None
    is_active: bool
    created_at: datetime.datetime


# ==================== Seat Schemas ====================

# Schema for creating a single seat within a category
class SeatCreate(BaseSchemaModel):
    """Schema for creating a seat"""
    # Foreign key to the seat category this seat belongs to
    category_id: int
    # Alphanumeric identifier (e.g., "A1", "B12")
    seat_number: str | None = pydantic.Field(None, max_length=20)
    # Row label (e.g., "A", "B", "AA")
    row_name: str | None = pydantic.Field(None, max_length=10)
    # Section of the venue (e.g., "Left Wing", "Orchestra")
    section: str | None = pydantic.Field(None, max_length=50)
    # X/Y coordinates for rendering the seat on an interactive seat map
    position_x: int | None = None
    position_y: int | None = None


# Schema for creating multiple seats at once across specified rows
class SeatBulkCreate(BaseSchemaModel):
    """Schema for bulk creating seats"""
    category_id: int
    section: str | None = None
    # List of row labels to create (e.g., ["A", "B", "C"])
    rows: list[str]  # ["A", "B", "C"]
    # Number of seats to create in each row (1-100)
    seats_per_row: int = pydantic.Field(..., ge=1, le=100)


# Schema for partially updating a seat
class SeatUpdate(BaseSchemaModel):
    """Schema for updating a seat"""
    category_id: int | None = None
    seat_number: str | None = pydantic.Field(None, max_length=20)
    row_name: str | None = pydantic.Field(None, max_length=10)
    section: str | None = pydantic.Field(None, max_length=50)
    status: str | None = None  # Only admin can change to 'blocked'
    position_x: int | None = None
    position_y: int | None = None


# Response schema for a single seat
class SeatResponse(BaseSchemaModel):
    """Schema for seat in responses"""
    id: int
    event_id: int
    category_id: int
    seat_number: str | None = None
    row_name: str | None = None
    section: str | None = None
    # Current status: available, locked, booked, or blocked
    status: str
    # Human-readable label combining row and seat number (e.g., "A-1")
    seat_label: str | None = None
    position_x: int | None = None
    position_y: int | None = None


# Lightweight seat schema optimized for rendering the interactive seat map on the frontend
class SeatAvailabilityResponse(BaseSchemaModel):
    """Schema for seat availability (optimized for frontend)"""
    id: int
    category_id: int
    seat_label: str | None = None
    row_name: str | None = None
    section: str | None = None
    # Seat status: available, locked, booked, or blocked
    status: str  # available, locked, booked, blocked
    position_x: int | None = None
    position_y: int | None = None


# Aggregated response for an event's complete seating layout
class EventSeatsResponse(BaseSchemaModel):
    """Schema for event seats with categories"""
    event_id: int
    # All seat categories for this event
    categories: list[SeatCategoryResponse]
    # All individual seats with their availability status
    seats: list[SeatAvailabilityResponse]
    total_seats: int
    available_seats: int


# ==================== Filter/Search Schemas ====================

# Query parameters for searching and filtering events
class EventSearchParams(BaseSchemaModel):
    """Schema for event search parameters"""
    # Free-text search query matching title or description
    query: str | None = None
    # Filter by event category
    category: str | None = None
    # Filter by venue city
    city: str | None = None
    # Filter events occurring on or after this date
    date_from: datetime.date | None = None
    # Filter events occurring on or before this date
    date_to: datetime.date | None = None
    # Filter by event status (e.g., published, cancelled)
    status: str | None = None
    # Filter by minimum ticket price across seat categories
    min_price: Decimal | None = None
    # Filter by maximum ticket price across seat categories
    max_price: Decimal | None = None
