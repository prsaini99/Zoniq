import datetime
import random
import string

from loguru import logger

from src.config.manager import settings


class OTPService:
    """
    Service for generating and managing OTP codes.
    """

    def __init__(self):
        self.otp_length = 6
        self.otp_expiry_minutes = 10

    def generate_otp(self) -> str:
        """Generate a random numeric OTP code"""
        return "".join(random.choices(string.digits, k=self.otp_length))

    def get_expiry_time(self) -> datetime.datetime:
        """Get the expiry time for an OTP"""
        return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=self.otp_expiry_minutes
        )

    def get_expiry_seconds(self) -> int:
        """Get the expiry time in seconds"""
        return self.otp_expiry_minutes * 60


class SMSService:
    """
    Mock SMS service for sending OTP codes.
    Replace with actual implementation (Twilio, MSG91, etc.) in production.
    """

    async def send_otp(self, phone: str, code: str) -> bool:
        """
        Send OTP via SMS.
        Currently mocked - logs the OTP instead of sending.
        """
        logger.info(f"[MOCK SMS] Sending OTP {code} to phone {phone}")

        # In production, integrate with Twilio or other SMS provider:
        # from twilio.rest import Client
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        # message = client.messages.create(
        #     body=f"Your ZONIQ verification code is: {code}",
        #     from_=settings.TWILIO_PHONE_NUMBER,
        #     to=phone
        # )

        return True

    async def send_message(self, phone: str, message: str) -> bool:
        """
        Send a general SMS message.
        Currently mocked.
        """
        logger.info(f"[MOCK SMS] Sending message to {phone}: {message}")
        return True


class EmailService:
    """
    Mock Email service for sending OTP codes and notifications.
    Replace with actual implementation (SendGrid, AWS SES, etc.) in production.
    """

    async def send_otp(self, email: str, code: str) -> bool:
        """
        Send OTP via email.
        Currently mocked - logs the OTP instead of sending.
        """
        logger.info(f"[MOCK EMAIL] Sending OTP {code} to email {email}")

        # In production, integrate with SendGrid or AWS SES:
        # import sendgrid
        # sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        # message = Mail(
        #     from_email=settings.SENDGRID_FROM_EMAIL,
        #     to_emails=email,
        #     subject="Your ZONIQ Verification Code",
        #     html_content=f"<p>Your verification code is: <strong>{code}</strong></p>"
        # )
        # sg.send(message)

        return True

    async def send_password_reset(self, email: str, code: str) -> bool:
        """
        Send password reset OTP via email.
        Currently mocked.
        """
        logger.info(f"[MOCK EMAIL] Sending password reset OTP {code} to email {email}")
        return True

    async def send_welcome(self, email: str, username: str) -> bool:
        """
        Send welcome email to new user.
        Currently mocked.
        """
        logger.info(f"[MOCK EMAIL] Sending welcome email to {email} for user {username}")
        return True

    async def send_message(self, email: str, subject: str, body: str) -> bool:
        """
        Send a general email message.
        Currently mocked.
        """
        logger.info(f"[MOCK EMAIL] Sending email to {email}: {subject}")
        return True


# Singleton instances
otp_service = OTPService()
sms_service = SMSService()
email_service = EmailService()
