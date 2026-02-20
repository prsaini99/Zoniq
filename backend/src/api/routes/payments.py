# Payment routes for Razorpay integration: order creation, verification, webhooks, and booking cancellation
import logging

import fastapi
from fastapi import Depends, HTTPException, Request

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.config.manager import settings
from src.models.db.account import Account
from src.models.schemas.payment import (
    CreatePaymentOrderRequest,
    CreatePaymentOrderResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
)
from src.repository.crud.booking import BookingCRUDRepository
from src.repository.crud.payment import PaymentCRUDRepository
from src.services.razorpay_service import razorpay_service
from src.services.email_service import email_service as smtp_email_service
from src.utilities.exceptions.database import EntityDoesNotExist

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/payments", tags=["payments"])


# --- POST /payments/create-order ---
# Initiates the Razorpay payment flow by creating an order tied to a booking.
# The frontend uses the returned order_id and key_id to open Razorpay checkout.
@router.post(
    "/create-order",
    name="payments:create-order",
    response_model=CreatePaymentOrderResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def create_payment_order(
    request: CreatePaymentOrderRequest,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
    payment_repo: PaymentCRUDRepository = Depends(get_repository(repo_type=PaymentCRUDRepository)),
) -> CreatePaymentOrderResponse:
    """
    Create a Razorpay order for a booking.
    This initiates the payment flow - frontend will use this to open Razorpay checkout.
    """
    # Fetch the booking by ID; raise 404 if it does not exist
    try:
        booking = await booking_repo.read_booking_by_id(request.booking_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only the booking owner can create a payment order for it
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Prevent payment for bookings that are cancelled or in a non-payable state
    if booking.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=400, detail=f"Cannot pay for {booking.status} booking")

    # Guard against duplicate payments for an already-paid booking
    if booking.payment_status == "success":
        raise HTTPException(status_code=400, detail="Booking already paid")

    # Check if a previously created Razorpay order is still valid (status "created")
    # If so, return it to avoid creating duplicate orders
    existing_payment = await payment_repo.read_payment_by_booking_id(booking.id)
    if existing_payment and existing_payment.status == "created":
        # Attempt to fetch the order from Razorpay to verify it has not expired
        try:
            order = razorpay_service.fetch_order(existing_payment.razorpay_order_id)
            if order.get("status") == "created":
                return CreatePaymentOrderResponse(
                    order_id=existing_payment.razorpay_order_id,
                    amount=existing_payment.amount,
                    currency=existing_payment.currency,
                    key_id=settings.RAZORPAY_KEY_ID,
                    booking_id=booking.id,
                    booking_number=booking.booking_number,
                    user_name=current_user.full_name,
                    user_email=current_user.email,
                    user_phone=current_user.phone,
                )
        except Exception:
            pass  # Order expired or invalid, create new one

    # Razorpay expects the amount in the smallest currency unit (paise for INR)
    amount_paise = int(float(booking.final_amount) * 100)

    # Create a new Razorpay order with booking metadata stored in notes
    try:
        order = razorpay_service.create_order(
            amount_paise=amount_paise,
            currency="INR",
            receipt=booking.booking_number,
            notes={
                "booking_id": str(booking.id),
                "booking_number": booking.booking_number,
                "user_id": str(current_user.id),
            }
        )
    except Exception as e:
        logger.error(f"Failed to create Razorpay order: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")

    # Persist the payment record in the database linked to the booking and Razorpay order
    await payment_repo.create_payment(
        booking_id=booking.id,
        user_id=current_user.id,
        razorpay_order_id=order["id"],
        amount=amount_paise,
        currency="INR",
    )

    # Return the order details needed by the frontend to launch Razorpay checkout
    return CreatePaymentOrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        key_id=settings.RAZORPAY_KEY_ID,
        booking_id=booking.id,
        booking_number=booking.booking_number,
        user_name=current_user.full_name,
        user_email=current_user.email,
        user_phone=current_user.phone,
    )


# --- POST /payments/verify ---
# Called by the frontend after the user completes Razorpay checkout.
# Verifies the payment signature, marks payment as successful, and sends a confirmation email.
@router.post(
    "/verify",
    name="payments:verify-payment",
    response_model=VerifyPaymentResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: Account = Depends(get_current_user),
    payment_repo: PaymentCRUDRepository = Depends(get_repository(repo_type=PaymentCRUDRepository)),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> VerifyPaymentResponse:
    """
    Verify a Razorpay payment after successful checkout.
    This should be called from frontend after Razorpay checkout completes.
    """
    # Look up the internal payment record using the Razorpay order ID
    try:
        payment = await payment_repo.read_payment_by_order_id(request.razorpay_order_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Payment order not found")

    # Ensure the authenticated user owns this payment
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # If this payment was already captured or refunded, return early with success
    if payment.status in ("captured", "refunded"):
        booking = await booking_repo.read_booking_by_id(payment.booking_id)
        return VerifyPaymentResponse(
            success=True,
            booking_id=payment.booking_id,
            booking_number=booking.booking_number,
            message="Payment already verified",
        )

    # Verify the cryptographic signature from Razorpay to confirm payment authenticity
    is_valid = razorpay_service.verify_payment_signature(
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
    )

    # If signature verification fails, mark the payment as failed and reject the request
    if not is_valid:
        await payment_repo.update_payment_failed(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            error_code="SIGNATURE_MISMATCH",
            error_description="Payment signature verification failed",
        )
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Fetch the payment method (UPI, card, etc.) from Razorpay for record-keeping
    try:
        payment_details = razorpay_service.fetch_payment(request.razorpay_payment_id)
        method = payment_details.get("method")
    except Exception:
        method = None

    # Mark the payment as successfully captured in the database
    await payment_repo.update_payment_success(
        razorpay_order_id=request.razorpay_order_id,
        razorpay_payment_id=request.razorpay_payment_id,
        razorpay_signature=request.razorpay_signature,
        method=method,
    )

    # Retrieve the booking for the response and email content
    booking = await booking_repo.read_booking_by_id(payment.booking_id)

    # Send a payment confirmation email asynchronously (fire-and-forget)
    # Failures here are logged but do not block the API response
    try:
        await smtp_email_service.send_payment_confirmation(
            to_email=current_user.email,
            username=current_user.full_name or current_user.username,
            booking_number=booking.booking_number,
            payment_id=request.razorpay_payment_id,
            event_title=booking.event.title if booking.event else "Event",
            ticket_count=booking.ticket_count,
            amount=f"\u20b9{float(booking.final_amount):,.2f}",
        )
    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {str(e)}")

    return VerifyPaymentResponse(
        success=True,
        booking_id=payment.booking_id,
        booking_number=booking.booking_number,
        message="Payment successful",
    )


# --- GET /payments/{payment_id} ---
# Retrieves detailed payment information for a specific payment owned by the current user.
@router.get(
    "/{payment_id}",
    name="payments:get-payment",
    response_model=PaymentResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_payment(
    payment_id: int,
    current_user: Account = Depends(get_current_user),
    payment_repo: PaymentCRUDRepository = Depends(get_repository(repo_type=PaymentCRUDRepository)),
) -> PaymentResponse:
    """Get payment details by ID."""
    # Fetch the payment record; raise 404 if not found
    try:
        payment = await payment_repo.read_payment_by_id(payment_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Enforce ownership: only the paying user can view their payment details
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Return the full payment details including status, method, and any error info
    return PaymentResponse(
        id=payment.id,
        booking_id=payment.booking_id,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        method=payment.method,
        error_code=payment.error_code,
        error_description=payment.error_description,
        created_at=payment.created_at,
        paid_at=payment.paid_at,
    )


# --- POST /payments/webhook ---
# Server-to-server endpoint called by Razorpay to notify about payment events.
# No user auth is required; instead, the request is verified via webhook signature.
# Handles payment.captured, payment.failed, and refund events.
@router.post(
    "/webhook",
    name="payments:webhook",
    status_code=fastapi.status.HTTP_200_OK,
)
async def payment_webhook(
    request: Request,
    payment_repo: PaymentCRUDRepository = Depends(get_repository(repo_type=PaymentCRUDRepository)),
):
    """
    Razorpay webhook handler for payment events.
    This is called by Razorpay to notify about payment status changes.
    """
    # Read the raw request body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Validate the webhook signature using the shared secret to prevent spoofing
    if not razorpay_service.verify_webhook_signature(body, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Parse the JSON event payload from Razorpay
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event", "")
    event_payload = payload.get("payload", {})

    logger.info(f"Received Razorpay webhook: {event}")

    # Handle "payment.captured" -- payment was successfully captured
    if event == "payment.captured":
        payment_entity = event_payload.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        method = payment_entity.get("method")

        if order_id:
            # Update the internal payment record to reflect successful capture
            try:
                await payment_repo.update_payment_success(
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                    razorpay_signature="",  # Not available in webhook
                    method=method,
                )
                logger.info(f"Payment captured via webhook: {order_id}")
            except EntityDoesNotExist:
                logger.warning(f"Payment order not found: {order_id}")

    # Handle "payment.failed" -- payment attempt failed
    elif event == "payment.failed":
        payment_entity = event_payload.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        error = payment_entity.get("error_code")
        error_desc = payment_entity.get("error_description")

        if order_id:
            try:
                # Mark the payment as failed with error details from Razorpay
                payment = await payment_repo.update_payment_failed(
                    razorpay_order_id=order_id,
                    razorpay_payment_id=payment_id,
                    error_code=error,
                    error_description=error_desc,
                )
                logger.info(f"Payment failed via webhook: {order_id}")

                # Release the reserved seats so other users can book them
                if payment and payment.booking_id:
                    booking_repo = BookingCRUDRepository(payment_repo.async_session)
                    await booking_repo.release_seats_for_failed_payment(payment.booking_id)
                    logger.info(f"Released seats for failed payment booking: {payment.booking_id}")
            except EntityDoesNotExist:
                logger.warning(f"Payment order not found: {order_id}")
            except Exception as e:
                logger.error(f"Error releasing seats for failed payment: {str(e)}")

    # Handle refund events (created or fully processed)
    elif event == "refund.created" or event == "refund.processed":
        refund_entity = event_payload.get("refund", {}).get("entity", {})
        payment_id = refund_entity.get("payment_id")
        refund_id = refund_entity.get("id")
        amount = refund_entity.get("amount", 0)
        status = "processed" if event == "refund.processed" else "pending"

        if payment_id:
            # Log the refund event; full refund processing is not yet implemented
            try:
                logger.info(f"Refund {status}: {refund_id} for payment {payment_id}")
            except Exception as e:
                logger.error(f"Error processing refund webhook: {str(e)}")

    # Acknowledge receipt of the webhook to Razorpay
    return {"status": "ok"}


# --- POST /payments/booking/{booking_id}/cancel ---
# Allows a user to cancel a pending (unpaid) booking and release the reserved seats.
# Typically invoked when the user dismisses the payment modal or abandons checkout.
@router.post(
    "/booking/{booking_id}/cancel",
    name="payments:cancel-pending-booking",
    status_code=fastapi.status.HTTP_200_OK,
)
async def cancel_pending_booking(
    booking_id: int,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
):
    """
    Cancel a pending booking and release its seats.
    Used when user cancels payment or payment modal is dismissed.
    """
    # Retrieve the booking; raise 404 if it does not exist
    try:
        booking = await booking_repo.read_booking_by_id(booking_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Only the booking owner can cancel their own booking
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only bookings in "pending" status can be cancelled; confirmed/paid bookings cannot
    if booking.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot cancel booking with status '{booking.status}'")

    # Release the seats that were held for this booking back into availability
    await booking_repo.release_seats_for_failed_payment(booking_id)

    return {"success": True, "message": "Booking cancelled and seats released"}


# --- GET /payments/booking/{booking_id}/status ---
# Returns the current payment status for a given booking, including payment method and timestamps.
@router.get(
    "/booking/{booking_id}/status",
    name="payments:get-payment-status",
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_payment_status_for_booking(
    booking_id: int,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
    payment_repo: PaymentCRUDRepository = Depends(get_repository(repo_type=PaymentCRUDRepository)),
):
    """Get payment status for a booking."""
    # Verify the booking exists and belongs to the current user
    try:
        booking = await booking_repo.read_booking_by_id(booking_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Look up the associated payment record for this booking
    payment = await payment_repo.read_payment_by_booking_id(booking_id)

    # If no payment record exists, return the booking-level payment status only
    if not payment:
        return {
            "booking_id": booking_id,
            "payment_status": booking.payment_status,
            "payment": None,
        }

    # Return both booking-level and payment-level details
    return {
        "booking_id": booking_id,
        "payment_status": booking.payment_status,
        "payment": {
            "id": payment.id,
            "order_id": payment.razorpay_order_id,
            "payment_id": payment.razorpay_payment_id,
            "status": payment.status,
            "amount": payment.amount,
            "method": payment.method,
            "paid_at": payment.paid_at,
        },
    }
