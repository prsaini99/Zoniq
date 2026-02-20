# Ticket schemas for viewing tickets, marking usage, and transferring tickets between users
import datetime
from decimal import Decimal

import pydantic


# Schema for a single ticket with full event and booking context
class TicketResponse(pydantic.BaseModel):
    """Response for a single ticket."""
    id: int
    # The booking this ticket belongs to
    booking_id: int
    # Unique ticket identifier used for entry scanning/validation
    ticket_number: str
    # Name of the seat category (e.g., "VIP", "General")
    category_name: str
    # Human-readable seat label (e.g., "A-12"); None for general admission
    seat_label: str | None
    # Price paid for this ticket
    price: Decimal
    # Whether this ticket has been scanned/used at the event venue
    is_used: bool
    # Timestamp when the ticket was scanned/used
    used_at: datetime.datetime | None
    created_at: datetime.datetime

    # Event details associated with this ticket
    event_id: int
    event_title: str
    event_date: datetime.datetime
    venue_name: str | None
    venue_city: str | None

    # Parent booking reference info
    booking_number: str
    # Status of the parent booking (e.g., confirmed, cancelled)
    booking_status: str

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for organizers to mark a ticket as used (scanned at entry)
class MarkTicketUsedRequest(pydantic.BaseModel):
    """Request to mark a ticket as used (for organizers)."""
    # The unique ticket number to mark as used
    ticket_number: str


# Response after attempting to mark a ticket as used
class MarkTicketUsedResponse(pydantic.BaseModel):
    """Response after marking ticket as used."""
    success: bool
    ticket_number: str
    message: str
    # Timestamp when the ticket was marked as used (None if it failed)
    used_at: datetime.datetime | None = None

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for transferring a ticket to another user via email
class TransferTicketRequest(pydantic.BaseModel):
    """Request to transfer a ticket to another user."""
    # Email address of the person receiving the ticket
    to_email: pydantic.EmailStr
    # Optional message to include with the transfer notification
    message: str | None = None


# Response after initiating a ticket transfer
class TransferTicketResponse(pydantic.BaseModel):
    """Response after initiating ticket transfer."""
    success: bool
    # Internal ID of the transfer record
    transfer_id: int
    message: str
    # Deadline by which the recipient must claim the ticket
    expires_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for the recipient to claim a transferred ticket using a token
class ClaimTransferRequest(pydantic.BaseModel):
    """Request to claim a transferred ticket."""
    # Unique token sent to the recipient's email for claiming the ticket
    transfer_token: str


# Response after attempting to claim a transferred ticket
class ClaimTransferResponse(pydantic.BaseModel):
    """Response after claiming a transferred ticket."""
    success: bool
    # The ticket number of the claimed ticket (None if claim failed)
    ticket_number: str | None = None
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


# Response after the original owner cancels a pending ticket transfer
class CancelTransferResponse(pydantic.BaseModel):
    """Response after cancelling a ticket transfer."""
    success: bool
    message: str

    model_config = pydantic.ConfigDict(from_attributes=True)


# Schema for a single entry in the ticket transfer history
class TransferHistoryItem(pydantic.BaseModel):
    """Single item in transfer history."""
    id: int
    ticket_number: str
    # Email of the user who initiated the transfer
    from_email: str
    # Email of the intended recipient
    to_email: str
    # Transfer status (e.g., pending, completed, cancelled, expired)
    status: str
    # Optional message included by the sender
    message: str | None
    created_at: datetime.datetime
    # When the transfer was completed (ticket claimed)
    transferred_at: datetime.datetime | None
    # Deadline for claiming the transfer
    expires_at: datetime.datetime

    model_config = pydantic.ConfigDict(from_attributes=True)


# Paginated response containing transfer history records
class TransferHistoryResponse(pydantic.BaseModel):
    """Response containing transfer history."""
    transfers: list[TransferHistoryItem]
    total: int

    model_config = pydantic.ConfigDict(from_attributes=True)
