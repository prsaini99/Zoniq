import hashlib
import hmac
import logging
from typing import Any

import razorpay

from src.config.manager import settings

# Configure module-level logger for payment operations
logger = logging.getLogger(__name__)


# Service class for integrating with the Razorpay payment gateway
class RazorpayService:
    """
    Service for Razorpay payment gateway integration.
    """

    # Load Razorpay API credentials and webhook secret from application settings
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        # Internal client instance — lazily initialized on first access
        self._client = None

    # Lazily initialize and return the Razorpay SDK client, validating credentials first
    @property
    def client(self) -> razorpay.Client:
        """Lazy initialization of Razorpay client."""
        if self._client is None:
            if not self.key_id or not self.key_secret:
                raise ValueError("Razorpay credentials not configured")
            self._client = razorpay.Client(auth=(self.key_id, self.key_secret))
        return self._client

    # Create a new payment order on Razorpay with the specified amount, currency, and metadata
    def create_order(
        self,
        amount_paise: int,
        currency: str = "INR",
        receipt: str | None = None,
        notes: dict | None = None,
    ) -> dict[str, Any]:
        """
        Create a Razorpay order.

        Args:
            amount_paise: Amount in paise (smallest currency unit)
            currency: Currency code (default: INR)
            receipt: Optional receipt/reference ID
            notes: Optional metadata

        Returns:
            Razorpay order response with order_id
        """
        # Build the order payload with auto-capture enabled
        order_data = {
            "amount": amount_paise,
            "currency": currency,
            "payment_capture": 1,  # Auto-capture payment
        }
        # Include optional receipt reference if provided
        if receipt:
            order_data["receipt"] = receipt
        # Include optional notes/metadata if provided
        if notes:
            order_data["notes"] = notes

        try:
            # Call Razorpay API to create the order
            order = self.client.order.create(data=order_data)
            logger.info(f"Created Razorpay order: {order['id']} for amount {amount_paise}")
            return order
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise

    # Verify the cryptographic signature returned by Razorpay after a payment is completed
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify the payment signature from Razorpay.

        Args:
            razorpay_order_id: The Razorpay order ID
            razorpay_payment_id: The Razorpay payment ID
            razorpay_signature: The signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Use Razorpay SDK utility to verify the payment signature
            self.client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            logger.info(f"Payment signature verified for order: {razorpay_order_id}")
            return True
        except razorpay.errors.SignatureVerificationError:
            # Signature mismatch — possible tampering or incorrect data
            logger.warning(f"Invalid payment signature for order: {razorpay_order_id}")
            return False
        except Exception as e:
            logger.error(f"Error verifying payment signature: {str(e)}")
            return False

    # Retrieve full payment details from Razorpay by payment ID
    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """
        Fetch payment details from Razorpay.

        Args:
            payment_id: The Razorpay payment ID

        Returns:
            Payment details
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch payment {payment_id}: {str(e)}")
            raise

    # Retrieve full order details from Razorpay by order ID
    def fetch_order(self, order_id: str) -> dict[str, Any]:
        """
        Fetch order details from Razorpay.

        Args:
            order_id: The Razorpay order ID

        Returns:
            Order details
        """
        try:
            order = self.client.order.fetch(order_id)
            return order
        except Exception as e:
            logger.error(f"Failed to fetch order {order_id}: {str(e)}")
            raise

    # Issue a full or partial refund for a previously captured payment
    def refund_payment(
        self,
        payment_id: str,
        amount_paise: int | None = None,
        notes: dict | None = None,
    ) -> dict[str, Any]:
        """
        Create a refund for a payment.

        Args:
            payment_id: The Razorpay payment ID
            amount_paise: Amount to refund in paise (None for full refund)
            notes: Optional metadata

        Returns:
            Refund response
        """
        refund_data = {}
        # If amount specified, perform a partial refund; otherwise full refund
        if amount_paise:
            refund_data["amount"] = amount_paise
        if notes:
            refund_data["notes"] = notes

        try:
            refund = self.client.payment.refund(payment_id, refund_data)
            logger.info(f"Created refund for payment {payment_id}: {refund['id']}")
            return refund
        except Exception as e:
            logger.error(f"Failed to create refund for payment {payment_id}: {str(e)}")
            raise

    # Verify the HMAC-SHA256 signature on incoming Razorpay webhook requests
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            body: Raw request body
            signature: X-Razorpay-Signature header

        Returns:
            True if valid, False otherwise
        """
        # Skip verification if no webhook secret is configured
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping verification")
            return True

        try:
            # Compute expected HMAC-SHA256 signature using the webhook secret
            expected_signature = hmac.new(
                key=self.webhook_secret.encode("utf-8"),
                msg=body,
                digestmod=hashlib.sha256
            ).hexdigest()
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False


# Singleton instance — shared across the application for all Razorpay operations
razorpay_service = RazorpayService()
