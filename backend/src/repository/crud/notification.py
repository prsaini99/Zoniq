# Notification CRUD repository -- manages per-user email notification preferences.
# Provides get-or-create semantics for preferences, granular updates for each
# notification type, and a lookup method to check whether a specific email type
# should be sent to a given user.

import logging
from datetime import datetime

import sqlalchemy
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db.notification_preference import NotificationPreference
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist

logger = logging.getLogger(__name__)


class NotificationCRUDRepository(BaseCRUDRepository):
    """Repository for notification preference operations."""

    # Retrieves the user's notification preferences. If no preferences record exists
    # yet (e.g., new user), creates one with default values and persists it.
    async def get_or_create_preferences(self, user_id: int) -> NotificationPreference:
        """Get notification preferences for a user, creating defaults if not exists."""
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await self.async_session.execute(stmt)
        preferences = result.scalar_one_or_none()

        if not preferences:
            # Create default preferences
            # Default values are defined in the NotificationPreference model.
            preferences = NotificationPreference(user_id=user_id)
            self.async_session.add(preferences)
            await self.async_session.commit()
            await self.async_session.refresh(preferences)

        return preferences

    # Updates individual notification preference flags for a user.
    # Only fields explicitly passed (non-None) are updated; others remain unchanged.
    # Covers all email notification types: booking confirmations, payment updates,
    # ticket delivery, event reminders/updates, transfer notifications, and marketing.
    async def update_preferences(
        self,
        user_id: int,
        email_booking_confirmation: bool | None = None,
        email_payment_updates: bool | None = None,
        email_ticket_delivery: bool | None = None,
        email_event_reminders: bool | None = None,
        email_event_updates: bool | None = None,
        email_transfer_notifications: bool | None = None,
        email_marketing: bool | None = None,
    ) -> NotificationPreference:
        """Update notification preferences for a user."""
        # Ensure preferences exist
        preferences = await self.get_or_create_preferences(user_id)

        # Build update dict with only provided values
        update_data = {}
        if email_booking_confirmation is not None:
            update_data["email_booking_confirmation"] = email_booking_confirmation
        if email_payment_updates is not None:
            update_data["email_payment_updates"] = email_payment_updates
        if email_ticket_delivery is not None:
            update_data["email_ticket_delivery"] = email_ticket_delivery
        if email_event_reminders is not None:
            update_data["email_event_reminders"] = email_event_reminders
        if email_event_updates is not None:
            update_data["email_event_updates"] = email_event_updates
        if email_transfer_notifications is not None:
            update_data["email_transfer_notifications"] = email_transfer_notifications
        if email_marketing is not None:
            update_data["email_marketing"] = email_marketing

        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            stmt = (
                update(NotificationPreference)
                .where(NotificationPreference.user_id == user_id)
                .values(**update_data)
            )
            await self.async_session.execute(stmt)
            await self.async_session.commit()
            await self.async_session.refresh(preferences)

        return preferences

    # Checks whether a specific email notification type is enabled for a user.
    # Maps email_type strings (e.g., "booking_confirmation") to the corresponding
    # preference boolean. Returns True by default for unknown types to avoid
    # accidentally suppressing important emails.
    async def should_send_email(self, user_id: int, email_type: str) -> bool:
        """
        Check if a specific email type should be sent to the user.

        Args:
            user_id: The user's ID
            email_type: One of 'booking_confirmation', 'payment_updates',
                       'ticket_delivery', 'event_reminders', 'event_updates',
                       'transfer_notifications', 'marketing'
        """
        preferences = await self.get_or_create_preferences(user_id)

        # Map email type strings to their corresponding preference attribute values.
        type_mapping = {
            "booking_confirmation": preferences.email_booking_confirmation,
            "payment_updates": preferences.email_payment_updates,
            "ticket_delivery": preferences.email_ticket_delivery,
            "event_reminders": preferences.email_event_reminders,
            "event_updates": preferences.email_event_updates,
            "transfer_notifications": preferences.email_transfer_notifications,
            "marketing": preferences.email_marketing,
        }

        # Default to True for unrecognized types as a safety measure.
        return type_mapping.get(email_type, True)
