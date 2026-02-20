# Notification preference schemas for managing user email notification settings
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Response schema exposing the user's current notification preference settings
class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""

    # Whether to receive email when a booking is confirmed
    email_booking_confirmation: bool = Field(
        ..., description="Receive booking confirmation emails"
    )
    # Whether to receive email on payment success or failure
    email_payment_updates: bool = Field(
        ..., description="Receive payment success/failure emails"
    )
    # Whether to receive the ticket delivery email with ticket details
    email_ticket_delivery: bool = Field(
        ..., description="Receive ticket delivery emails"
    )
    # Whether to receive reminder emails before the event date
    email_event_reminders: bool = Field(
        ..., description="Receive event reminder emails"
    )
    # Whether to receive emails about event changes or cancellations
    email_event_updates: bool = Field(
        ..., description="Receive event update/cancellation emails"
    )
    # Whether to receive emails about incoming or outgoing ticket transfers
    email_transfer_notifications: bool = Field(
        ..., description="Receive ticket transfer notifications"
    )
    # Whether to receive promotional and marketing emails
    email_marketing: bool = Field(
        ..., description="Receive marketing and promotional emails"
    )
    # When the preferences were first created
    created_at: datetime
    # When the preferences were last modified
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Request schema for updating notification preferences (all fields optional for partial updates)
class NotificationPreferenceUpdate(BaseModel):
    """Request schema for updating notification preferences."""

    email_booking_confirmation: Optional[bool] = Field(
        None, description="Receive booking confirmation emails"
    )
    email_payment_updates: Optional[bool] = Field(
        None, description="Receive payment success/failure emails"
    )
    email_ticket_delivery: Optional[bool] = Field(
        None, description="Receive ticket delivery emails"
    )
    email_event_reminders: Optional[bool] = Field(
        None, description="Receive event reminder emails"
    )
    email_event_updates: Optional[bool] = Field(
        None, description="Receive event update/cancellation emails"
    )
    email_transfer_notifications: Optional[bool] = Field(
        None, description="Receive ticket transfer notifications"
    )
    email_marketing: Optional[bool] = Field(
        None, description="Receive marketing and promotional emails"
    )
