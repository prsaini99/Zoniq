# Venue schemas for creating, updating, and responding with venue/location data
import datetime
from typing import Any

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

# Schema for creating a new venue (event location)
class VenueCreate(BaseSchemaModel):
    """Schema for creating a new venue"""
    # Venue name, required, 1-255 characters
    name: str = pydantic.Field(..., min_length=1, max_length=255)
    # Full street address of the venue
    address: str | None = None
    # City where the venue is located
    city: str | None = pydantic.Field(None, max_length=100)
    # State or province
    state: str | None = pydantic.Field(None, max_length=100)
    # Country, defaults to India
    country: str | None = pydantic.Field(default="India", max_length=100)
    # Postal/ZIP code
    pincode: str | None = pydantic.Field(None, max_length=20)
    # Maximum seating capacity of the venue
    capacity: int | None = pydantic.Field(None, ge=1)
    # JSON configuration for rendering the interactive seat map
    seat_map_config: dict[str, Any] | None = None
    # Venue contact phone number
    contact_phone: str | None = pydantic.Field(None, max_length=20)
    # Venue contact email address
    contact_email: pydantic.EmailStr | None = None


# Schema for partially updating an existing venue (all fields optional)
class VenueUpdate(BaseSchemaModel):
    """Schema for updating a venue"""
    name: str | None = pydantic.Field(None, min_length=1, max_length=255)
    address: str | None = None
    city: str | None = pydantic.Field(None, max_length=100)
    state: str | None = pydantic.Field(None, max_length=100)
    country: str | None = pydantic.Field(None, max_length=100)
    pincode: str | None = pydantic.Field(None, max_length=20)
    capacity: int | None = pydantic.Field(None, ge=1)
    seat_map_config: dict[str, Any] | None = None
    contact_phone: str | None = pydantic.Field(None, max_length=20)
    contact_email: pydantic.EmailStr | None = None
    # Whether the venue is active and can be assigned to events
    is_active: bool | None = None


# ==================== Response Schemas ====================

# Standard venue response with core details (excludes seat map config for performance)
class VenueResponse(BaseSchemaModel):
    """Schema for venue in responses"""
    id: int
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    pincode: str | None = None
    capacity: int | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None


# Extended venue response that includes the seat map configuration JSON
class VenueDetailResponse(VenueResponse):
    """Schema for detailed venue response (includes seat map config)"""
    seat_map_config: dict[str, Any] | None = None


# Paginated list of venues for listing endpoints
class VenueListResponse(BaseSchemaModel):
    """Schema for paginated venue list"""
    venues: list[VenueResponse]
    total: int
    page: int
    page_size: int


# ==================== Compact Schemas ====================

# Minimal venue info for embedding inside event responses to avoid redundant data
class VenueCompact(BaseSchemaModel):
    """Compact venue info for embedding in other responses"""
    id: int
    name: str
    city: str | None = None
    state: str | None = None
