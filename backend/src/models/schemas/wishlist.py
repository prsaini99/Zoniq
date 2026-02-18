"""
Wishlist Pydantic Schemas
"""
import datetime
import pydantic

from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.event import EventResponse


class WishlistItemResponse(BaseSchemaModel):
    """Schema for a wishlist item"""
    id: int
    event_id: int
    event: EventResponse
    created_at: datetime.datetime


class WishlistResponse(BaseSchemaModel):
    """Schema for user's full wishlist"""
    items: list[WishlistItemResponse]
    total: int


class WishlistCheckResponse(BaseSchemaModel):
    """Schema for checking if event is in wishlist"""
    is_in_wishlist: bool = pydantic.Field(alias="isInWishlist")
