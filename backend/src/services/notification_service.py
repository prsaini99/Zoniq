import logging
from datetime import datetime
from typing import Optional

from src.services.email_service import email_service
from src.repository.crud.notification import NotificationCRUDRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications with preference checking.

    This service wraps the email service and checks user preferences
    before sending emails.
    """

    def __init__(self):
        self.email = email_service

    async def send_booking_confirmation(
        self,
        notification_repo: NotificationCRUDRepository,
        user_id: int,
        to_email: str,
        booking_number: str,
        event_title: str,
        event_date: datetime,
        venue_name: str,
        ticket_count: int,
        total_amount: str,
        tickets: list[dict],
        pdf_attachment: Optional[tuple[str, bytes]] = None,
    ) -> bool:
        """Send booking confirmation email if user has enabled it."""
        if not await notification_repo.should_send_email(user_id, "booking_confirmation"):
            logger.info(f"User {user_id} has disabled booking confirmation emails")
            return False

        return await self.email.send_booking_confirmation(
            to_email=to_email,
            booking_number=booking_number,
            event_title=event_title,
            event_date=event_date.strftime("%B %d, %Y at %I:%M %p"),
            venue_name=venue_name,
            ticket_count=ticket_count,
            total_amount=total_amount,
            tickets=tickets,
            pdf_attachment=pdf_attachment,
        )


# Singleton instance
notification_service = NotificationService()
