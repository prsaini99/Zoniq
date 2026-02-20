# Notification preference routes: retrieve and update per-user email notification settings
import logging

import fastapi
from fastapi import Depends, HTTPException

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from src.repository.crud.notification import NotificationCRUDRepository

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/users/me/notifications", tags=["notifications"])


# --- GET /users/me/notifications/preferences ---
# Returns the current user's notification preferences.
# If no preferences exist yet, a default set is created automatically (opt-in by default).
@router.get(
    "/preferences",
    name="notifications:get-preferences",
    response_model=NotificationPreferenceResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_notification_preferences(
    current_user: Account = Depends(get_current_user),
    notification_repo: NotificationCRUDRepository = Depends(
        get_repository(repo_type=NotificationCRUDRepository)
    ),
) -> NotificationPreferenceResponse:
    """Get notification preferences for the current user."""
    # Fetch existing preferences or create defaults if this is the user's first access
    preferences = await notification_repo.get_or_create_preferences(current_user.id)

    # Map the database model fields to the response schema
    return NotificationPreferenceResponse(
        email_booking_confirmation=preferences.email_booking_confirmation,
        email_payment_updates=preferences.email_payment_updates,
        email_ticket_delivery=preferences.email_ticket_delivery,
        email_event_reminders=preferences.email_event_reminders,
        email_event_updates=preferences.email_event_updates,
        email_transfer_notifications=preferences.email_transfer_notifications,
        email_marketing=preferences.email_marketing,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


# --- PATCH /users/me/notifications/preferences ---
# Partially updates the user's notification preferences.
# Only the fields provided in the request body are updated; omitted fields remain unchanged.
# Each field controls whether a specific category of email notification is enabled or disabled.
@router.patch(
    "/preferences",
    name="notifications:update-preferences",
    response_model=NotificationPreferenceResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_notification_preferences(
    update_data: NotificationPreferenceUpdate,
    current_user: Account = Depends(get_current_user),
    notification_repo: NotificationCRUDRepository = Depends(
        get_repository(repo_type=NotificationCRUDRepository)
    ),
) -> NotificationPreferenceResponse:
    """Update notification preferences for the current user."""
    # Apply the partial update; None values in the request are skipped by the repository
    preferences = await notification_repo.update_preferences(
        user_id=current_user.id,
        email_booking_confirmation=update_data.email_booking_confirmation,
        email_payment_updates=update_data.email_payment_updates,
        email_ticket_delivery=update_data.email_ticket_delivery,
        email_event_reminders=update_data.email_event_reminders,
        email_event_updates=update_data.email_event_updates,
        email_transfer_notifications=update_data.email_transfer_notifications,
        email_marketing=update_data.email_marketing,
    )

    # Return the full updated preference set
    return NotificationPreferenceResponse(
        email_booking_confirmation=preferences.email_booking_confirmation,
        email_payment_updates=preferences.email_payment_updates,
        email_ticket_delivery=preferences.email_ticket_delivery,
        email_event_reminders=preferences.email_event_reminders,
        email_event_updates=preferences.email_event_updates,
        email_transfer_notifications=preferences.email_transfer_notifications,
        email_marketing=preferences.email_marketing,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )
