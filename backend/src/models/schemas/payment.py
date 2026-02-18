import datetime
from decimal import Decimal

import pydantic


class CreatePaymentOrderRequest(pydantic.BaseModel):
    """Request to create a Razorpay order for a booking."""
    booking_id: int


class CreatePaymentOrderResponse(pydantic.BaseModel):
    """Response containing Razorpay order details for frontend checkout."""
    order_id: str
    amount: int  # Amount in paise
    currency: str
    key_id: str  # Razorpay key ID for frontend
    booking_id: int
    booking_number: str
    user_name: str | None
    user_email: str
    user_phone: str | None

    model_config = pydantic.ConfigDict(from_attributes=True)


class VerifyPaymentRequest(pydantic.BaseModel):
    """Request to verify a Razorpay payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(pydantic.BaseModel):
    """Response after payment verification."""
    success: bool
    booking_id: int
    booking_number: str
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class PaymentResponse(pydantic.BaseModel):
    """Payment record response."""
    id: int
    booking_id: int
    razorpay_order_id: str
    razorpay_payment_id: str | None
    amount: int
    currency: str
    status: str
    method: str | None
    error_code: str | None
    error_description: str | None
    created_at: datetime.datetime
    paid_at: datetime.datetime | None

    model_config = pydantic.ConfigDict(from_attributes=True)


class PaymentWebhookEvent(pydantic.BaseModel):
    """Razorpay webhook event payload."""
    event: str
    payload: dict

    model_config = pydantic.ConfigDict(extra="allow")


class RefundRequest(pydantic.BaseModel):
    """Request to initiate a refund."""
    payment_id: int
    amount: int | None = None  # Partial refund amount in paise, None for full refund
    reason: str | None = None


class RefundResponse(pydantic.BaseModel):
    """Response after refund initiation."""
    success: bool
    refund_id: str | None
    amount: int
    status: str
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)
