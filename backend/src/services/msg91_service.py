import logging
from typing import Optional

import httpx

from src.config.manager import settings

logger = logging.getLogger(__name__)

MSG91_BASE_URL = "https://control.msg91.com/api/v5"


class MSG91Service:
    """
    Service for sending and verifying OTPs via MSG91.
    MSG91 manages OTP generation, sending, and verification internally.
    """

    def __init__(self):
        self.auth_key = settings.MSG91_AUTH_KEY
        self.template_id = settings.MSG91_OTP_TEMPLATE_ID

    @property
    def is_configured(self) -> bool:
        return bool(self.auth_key and self.template_id)

    async def send_otp(self, phone: str, otp_expiry: int = 10) -> dict:
        """
        Send OTP to a phone number via MSG91.

        Args:
            phone: Phone number with country code (e.g., "919876543210")
            otp_expiry: OTP expiry time in minutes

        Returns:
            MSG91 API response dict
        """
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - logging OTP request for phone: %s", phone)
            return {"request_id": "mock", "type": "mock"}

        url = f"{MSG91_BASE_URL}/otp"
        params = {
            "template_id": self.template_id,
            "mobile": phone,
            "authkey": self.auth_key,
            "otp_expiry": otp_expiry,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Send OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to send OTP to %s: %s", phone, str(e))
            raise

    async def verify_otp(self, phone: str, otp: str) -> dict:
        """
        Verify OTP for a phone number via MSG91.

        Args:
            phone: Phone number with country code
            otp: The OTP code entered by user

        Returns:
            MSG91 API response dict
        """
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - mock verifying OTP for phone: %s", phone)
            return {"type": "success", "message": "OTP verified successfully (mock)"}

        url = f"{MSG91_BASE_URL}/otp/verify"
        params = {
            "mobile": phone,
            "otp": otp,
            "authkey": self.auth_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Verify OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to verify OTP for %s: %s", phone, str(e))
            raise

    async def resend_otp(self, phone: str, retrytype: str = "text") -> dict:
        """
        Resend OTP to a phone number via MSG91.

        Args:
            phone: Phone number with country code
            retrytype: "text" for SMS, "voice" for voice call

        Returns:
            MSG91 API response dict
        """
        if not self.is_configured:
            logger.warning("[MSG91] Not configured - mock resending OTP for phone: %s", phone)
            return {"request_id": "mock", "type": "mock"}

        url = f"{MSG91_BASE_URL}/otp/retry"
        params = {
            "mobile": phone,
            "authkey": self.auth_key,
            "retrytype": retrytype,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, params=params)
                data = response.json()
                logger.info("[MSG91] Resend OTP response for %s: %s", phone, data)
                return data
        except Exception as e:
            logger.error("[MSG91] Failed to resend OTP to %s: %s", phone, str(e))
            raise


# Singleton instance
msg91_service = MSG91Service()
