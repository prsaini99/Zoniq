import logging
from typing import Optional

import httpx

from src.config.manager import settings

# Configure module-level logger for MSG91 operations
logger = logging.getLogger(__name__)

# Base URL for the MSG91 OTP API (v5)
MSG91_BASE_URL = "https://control.msg91.com/api/v5"


# Service class for sending and verifying OTPs via the MSG91 SMS gateway
class MSG91Service:
    """
    Service for sending and verifying OTPs via MSG91.
    MSG91 manages OTP generation, sending, and verification internally.
    """

    # Load MSG91 authentication key and OTP template ID from application settings
    def __init__(self):
        self.auth_key = settings.MSG91_AUTH_KEY
        self.template_id = settings.MSG91_OTP_TEMPLATE_ID

    # Check whether MSG91 credentials are properly configured
    @property
    def is_configured(self) -> bool:
        return bool(self.auth_key and self.template_id)

    # Send an OTP to the given phone number via MSG91; falls back to mock if not configured
    async def send_otp(self, phone: str, otp_expiry: int = 10) -> dict:
        """
        Send OTP to a phone number via MSG91.

        Args:
            phone: Phone number with country code (e.g., "919876543210")
            otp_expiry: OTP expiry time in minutes

        Returns:
            MSG91 API response dict
        """
        # If MSG91 is not configured, return a mock response for development
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - logging OTP request for phone: %s", phone)
            return {"request_id": "mock", "type": "mock"}

        # Build the request URL and query parameters for the MSG91 OTP endpoint
        url = f"{MSG91_BASE_URL}/otp"
        params = {
            "template_id": self.template_id,
            "mobile": phone,
            "authkey": self.auth_key,
            "otp_expiry": otp_expiry,
        }

        try:
            # Make an async HTTP POST request to MSG91 with a 10-second timeout
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Send OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to send OTP to %s: %s", phone, str(e))
            raise

    # Verify a user-entered OTP against MSG91's server-side record
    async def verify_otp(self, phone: str, otp: str) -> dict:
        """
        Verify OTP for a phone number via MSG91.

        Args:
            phone: Phone number with country code
            otp: The OTP code entered by user

        Returns:
            MSG91 API response dict
        """
        # Return a mock success response if MSG91 is not configured
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - mock verifying OTP for phone: %s", phone)
            return {"type": "success", "message": "OTP verified successfully (mock)"}

        # Build the verification request URL and parameters
        url = f"{MSG91_BASE_URL}/otp/verify"
        params = {
            "mobile": phone,
            "otp": otp,
            "authkey": self.auth_key,
        }

        try:
            # Make an async HTTP POST request to MSG91's OTP verification endpoint
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Verify OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to verify OTP for %s: %s", phone, str(e))
            raise

    # Resend an OTP to the given phone number, optionally via voice call instead of SMS
    async def resend_otp(self, phone: str, retrytype: str = "text") -> dict:
        """
        Resend OTP to a phone number via MSG91.

        Args:
            phone: Phone number with country code
            retrytype: "text" for SMS, "voice" for voice call

        Returns:
            MSG91 API response dict
        """
        # Return a mock response if MSG91 is not configured
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - mock resending OTP for phone: %s", phone)
            return {"request_id": "mock", "type": "mock"}

        # Build the retry request URL and parameters
        url = f"{MSG91_BASE_URL}/otp/retry"
        params = {
            "mobile": phone,
            "authkey": self.auth_key,
            "retrytype": retrytype,
        }

        try:
            # Make an async HTTP POST request to MSG91's OTP retry endpoint
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Resend OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to resend OTP to %s: %s", phone, str(e))
            raise


# Singleton instance — shared across the application for all MSG91 OTP operations
msg91_service = MSG91Service()
