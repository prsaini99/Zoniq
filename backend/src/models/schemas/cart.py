import datetime
from decimal import Decimal

import pydantic

from src.models.schemas.base import BaseSchemaModel


# ==================== Input Schemas ====================

class CartCreate(BaseSchemaModel):
    """Schema for creating/getting a cart"""
    event_id: int


class CartAddItem(BaseSchemaModel):
    """Schema for adding an item to cart"""
    event_id: int
    seat_category_id: int
    quantity: int = pydantic.Field(default=1, ge=1, le=10)
    seat_ids: list[int] | None = None  # For assigned seating


class CartUpdateItem(BaseSchemaModel):
    """Schema for updating cart item quantity"""
    quantity: int = pydantic.Field(ge=1, le=10)


class CheckoutRequest(BaseSchemaModel):
    """Schema for checkout"""
    contact_email: str | None = None
    contact_phone: str | None = None


# ==================== Response Schemas ====================

class CartItemResponse(BaseSchemaModel):
    """Schema for cart item in responses"""
    id: int
    seat_category_id: int
    category_name: str | None = None
    category_color: str | None = None
    seat_ids: list[int] | None = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    locked_until: datetime.datetime | None = None


class CartResponse(BaseSchemaModel):
    """Schema for cart in responses"""
    id: int
    user_id: int
    event_id: int
    event_title: str | None = None
    event_date: datetime.datetime | None = None
    event_image: str | None = None
    status: str
    items: list[CartItemResponse] = []
    subtotal: Decimal
    total: Decimal
    item_count: int
    expires_at: datetime.datetime


class CartValidationResponse(BaseSchemaModel):
    """Schema for cart validation result"""
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
