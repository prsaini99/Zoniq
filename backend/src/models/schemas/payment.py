# Payment schemas for Razorpay payment integration, verification, webhooks, and refunds
import datetime
from decimal import Decimal

import pydantic


# Schema for requesting creation of a Razorpay payment order linked to a booking
class CreatePaymentOrderRequest(pydantic.BaseModel):
    """Request to create a Razorpay order for a booking."""
    # The booking ID to create a payment order for
    booking_id: int


# Response containing Razorpay order details needed by the frontend to initiate checkout
class CreatePaymentOrderResponse(pydantic.BaseModel):
    """Response containing Razorpay order details for frontend checkout."""
    # Razorpay order ID to be used in the frontend checkout widget
    order_id: str
    # Payment amount in paise (smallest currency unit; 100 paise = 1 INR)
    amount: int  # Amount in paise
    # Currency code (e.g., "INR")
    currency: str
    # Razorpay public key ID for initializing the frontend checkout widget
    key_id: str  # Razorpay key ID for frontend
    # Booking reference details for display during payment
    booking_id: int
    booking_number: str
    # User details pre-filled in the payment form
    user_name: str | None
    user_email: str
    user_phone: str | None

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for verifying a completed Razorpay payment using signature validation
class VerifyPaymentRequest(pydantic.BaseModel):
    """Request to verify a Razorpay payment."""
    # The Razorpay order ID returned during order creation
    razorpay_order_id: str
    # The Razorpay payment ID generated after successful payment
    razorpay_payment_id: str
    # HMAC signature for verifying payment authenticity
    razorpay_signature: str


# Response returned after payment verification indicating success or failure
class VerifyPaymentResponse(pydantic.BaseModel):
    """Response after payment verification."""
    # Whether the payment was successfully verified
    success: bool
    booking_id: int
    booking_number: str
    # Human-readable status message
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema representing a stored payment record
class PaymentResponse(pydantic.BaseModel):
    """Payment record response."""
    id: int
    booking_id: int
    razorpay_order_id: str
    # Set after payment is completed; None while pending
    razorpay_payment_id: str | None
    # Amount in paise
    amount: int
    currency: str
    # Payment status (e.g., created, captured, failed)
    status: str
    # Payment method used (e.g., card, upi, netbanking)
    method: str | None
    # Error details if the payment failed
    error_code: str | None
    error_description: str | None
    created_at: datetime.datetime
    # Timestamp when the payment was successfully captured
    paid_at: datetime.datetime | None

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for incoming Razorpay webhook event payloads
class PaymentWebhookEvent(pydantic.BaseModel):
    """Razorpay webhook event payload."""
    # Event type string (e.g., "payment.captured", "payment.failed")
    event: str
    # Full event payload containing payment/order details
    payload: dict

    # Allow extra fields since Razorpay may add new fields to webhooks
    model_config = pydantic.ConfigDict(extra="allow")


# Schema for requesting a refund on a completed payment
class RefundRequest(pydantic.BaseModel):
    """Request to initiate a refund."""
    # The internal payment record ID to refund
    payment_id: int
    # Amount to refund in paise; None means full refund
    amount: int | None = None  # Partial refund amount in paise, None for full refund
    # Reason for the refund
    reason: str | None = None


# Response returned after a refund is initiated
class RefundResponse(pydantic.BaseModel):
    """Response after refund initiation."""
    success: bool
    # Razorpay refund ID (None if refund failed)
    refund_id: str | None
    # Refunded amount in paise
    amount: int
    # Refund status (e.g., processed, pending)
    status: str
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)
