import datetime
from typing import Any

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

class VenueCreate(BaseSchemaModel):
    """Schema for creating a new venue"""
    name: str = pydantic.Field(..., min_length=1, max_length=255)
    address: str | None = None
    city: str | None = pydantic.Field(None, max_length=100)
    state: str | None = pydantic.Field(None, max_length=100)
    country: str | None = pydantic.Field(default="India", max_length=100)
    pincode: str | None = pydantic.Field(None, max_length=20)
    capacity: int | None = pydantic.Field(None, ge=1)
    seat_map_config: dict[str, Any] | None = None
    contact_phone: str | None = pydantic.Field(None, max_length=20)
    contact_email: pydantic.EmailStr | None = None


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
    is_active: bool | None = None


# ==================== Response Schemas ====================

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


class VenueDetailResponse(VenueResponse):
    """Schema for detailed venue response (includes seat map config)"""
    seat_map_config: dict[str, Any] | None = None


class VenueListResponse(BaseSchemaModel):
    """Schema for paginated venue list"""
    venues: list[VenueResponse]
    total: int
    page: int
    page_size: int


# ==================== Compact Schemas ====================

class VenueCompact(BaseSchemaModel):
    """Compact venue info for embedding in other responses"""
    id: int
    name: str
    city: str | None = None
    state: str | None = None
