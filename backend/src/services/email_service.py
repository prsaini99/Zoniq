import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config.manager import settings

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "email"


class EmailService:
    """Service for sending emails using SMTP."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

        # Initialize Jinja2 template engine
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def _render_template(self, template_name: str, context: dict) -> str:
        """Render an email template with context."""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[list[tuple[str, bytes, str]]] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            attachments: List of (filename, content_bytes, mime_type) tuples

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text content
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            # Add HTML content
            msg.attach(MIMEText(html_content, "html"))

            # Add attachments
            if attachments:
                for filename, content, mime_type in attachments:
                    part = MIMEBase(*mime_type.split("/"))
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"',
                    )
                    msg.attach(part)

            # Send email
            if self.smtp_use_tls:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    start_tls=True,
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_booking_confirmation(
        self,
        to_email: str,
        booking_number: str,
        event_title: str,
        event_date: str,
        venue_name: str,
        ticket_count: int,
        total_amount: str,
        tickets: list[dict],
        pdf_attachment: Optional[tuple[str, bytes]] = None,
    ) -> bool:
        """Send booking confirmation email with optional PDF ticket attachment."""
        context = {
            "booking_number": booking_number,
            "event_title": event_title,
            "event_date": event_date,
            "venue_name": venue_name,
            "ticket_count": ticket_count,
            "total_amount": total_amount,
            "tickets": tickets,
            "app_name": "ZONIQ",
            "support_email": self.from_email,
        }

        html_content = self._render_template("booking_confirmation.html", context)
        subject = f"Booking Confirmed - {event_title} | ZONIQ"

        attachments = None
        if pdf_attachment:
            filename, content = pdf_attachment
            attachments = [(filename, content, "application/pdf")]

        return await self.send_email(to_email, subject, html_content, attachments=attachments)

    async def send_welcome(self, to_email: str, username: str) -> bool:
        """Send welcome/onboarded email to new user."""
        from src.config.manager import settings as app_settings

        context = {
            "username": username,
            "app_name": "ZONIQ",
            "support_email": self.from_email,
            "frontend_url": app_settings.FRONTEND_URL,
        }

        html_content = self._render_template("welcome.html", context)
        subject = f"Welcome to ZONIQ, {username}!"

        return await self.send_email(to_email, subject, html_content)

    async def send_otp_email(self, to_email: str, code: str, expires_minutes: int = 10) -> bool:
        """Send OTP verification code via email for login/signup."""
        context = {
            "code": code,
            "expires_minutes": expires_minutes,
            "app_name": "ZONIQ",
            "support_email": self.from_email,
        }

        html_content = self._render_template("otp_verification.html", context)
        subject = f"Your ZONIQ Verification Code: {code}"

        return await self.send_email(to_email, subject, html_content)

    async def send_payment_confirmation(
        self,
        to_email: str,
        username: str,
        booking_number: str,
        payment_id: str,
        event_title: str,
        ticket_count: int,
        amount: str,
    ) -> bool:
        """Send payment confirmation email."""
        from src.config.manager import settings as app_settings

        context = {
            "username": username,
            "booking_number": booking_number,
            "payment_id": payment_id,
            "event_title": event_title,
            "ticket_count": ticket_count,
            "amount": amount,
            "app_name": "ZONIQ",
            "support_email": self.from_email,
            "frontend_url": app_settings.FRONTEND_URL,
        }

        html_content = self._render_template("payment_confirmation.html", context)
        subject = f"Payment Confirmed - {event_title} | ZONIQ"

        return await self.send_email(to_email, subject, html_content)


# Singleton instance
email_service = EmailService()
