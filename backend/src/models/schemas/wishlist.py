# Wishlist schemas for managing user event wishlists (save/unsave events)
"""
Wishlist Pydantic Schemas
"""
import datetime
import pydantic

from src.models.schemas.base import BaseSchemaModel
from src.models.schemas.event import EventResponse


# Schema for a single wishlist entry containing the full event details
class WishlistItemResponse(BaseSchemaModel):
    """Schema for a wishlist item"""
    id: int
    # The event that was wishlisted
    event_id: int
    # Full event response object embedded for display purposes
    event: EventResponse
    # When the user added this event to their wishlist
    created_at: datetime.datetime


# Schema for the user's complete wishlist with pagination info
class WishlistResponse(BaseSchemaModel):
    """Schema for user's full wishlist"""
    # List of all wishlisted events
    items: list[WishlistItemResponse]
    # Total number of items in the wishlist
    total: int


# Schema for checking whether a specific event is in the user's wishlist
class WishlistCheckResponse(BaseSchemaModel):
    """Schema for checking if event is in wishlist"""
    # True if the event is currently in the user's wishlist
    is_in_wishlist: bool = pydantic.Field(alias="isInWishlist")
