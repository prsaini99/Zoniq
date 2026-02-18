from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""

    email_booking_confirmation: bool = Field(
        ..., description="Receive booking confirmation emails"
    )
    email_payment_updates: bool = Field(
        ..., description="Receive payment success/failure emails"
    )
    email_ticket_delivery: bool = Field(
        ..., description="Receive ticket delivery emails"
    )
    email_event_reminders: bool = Field(
        ..., description="Receive event reminder emails"
    )
    email_event_updates: bool = Field(
        ..., description="Receive event update/cancellation emails"
    )
    email_transfer_notifications: bool = Field(
        ..., description="Receive ticket transfer notifications"
    )
    email_marketing: bool = Field(
        ..., description="Receive marketing and promotional emails"
    )
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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
