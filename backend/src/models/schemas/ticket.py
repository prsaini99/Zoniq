import datetime
from decimal import Decimal

import pydantic


class TicketResponse(pydantic.BaseModel):
    """Response for a single ticket."""
    id: int
    booking_id: int
    ticket_number: str
    category_name: str
    seat_label: str | None
    price: Decimal
    is_used: bool
    used_at: datetime.datetime | None
    created_at: datetime.datetime

    # Event info
    event_id: int
    event_title: str
    event_date: datetime.datetime
    venue_name: str | None
    venue_city: str | None

    # Booking info
    booking_number: str
    booking_status: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class MarkTicketUsedRequest(pydantic.BaseModel):
    """Request to mark a ticket as used (for organizers)."""
    ticket_number: str


class MarkTicketUsedResponse(pydantic.BaseModel):
    """Response after marking ticket as used."""
    success: bool
    ticket_number: str
    message: str
    used_at: datetime.datetime | None = None

    model_config = pydantic.ConfigDict(from_attributes=True)


class TransferTicketRequest(pydantic.BaseModel):
    """Request to transfer a ticket to another user."""
    to_email: pydantic.EmailStr
    message: str | None = None


class TransferTicketResponse(pydantic.BaseModel):
    """Response after initiating ticket transfer."""
    success: bool
    transfer_id: int
    message: str
    expires_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class ClaimTransferRequest(pydantic.BaseModel):
    """Request to claim a transferred ticket."""
    transfer_token: str


class ClaimTransferResponse(pydantic.BaseModel):
    """Response after claiming a transferred ticket."""
    success: bool
    ticket_number: str | None = None
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class CancelTransferResponse(pydantic.BaseModel):
    """Response after cancelling a ticket transfer."""
    success: bool
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


class TransferHistoryItem(pydantic.BaseModel):
    """Single item in transfer history."""
    id: int
    ticket_number: str
    from_email: str
    to_email: str
    status: str
    message: str | None
    created_at: datetime.datetime
    transferred_at: datetime.datetime | None
    expires_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


class TransferHistoryResponse(pydantic.BaseModel):
    """Response containing transfer history."""
    transfers: list[TransferHistoryItem]
    total: int

    model_config = pydantic.ConfigDict(from_attributes=True)
