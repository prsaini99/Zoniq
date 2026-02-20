# Ticket routes: viewing, downloading PDFs, marking as used, transferring, and claiming tickets
import logging
from decimal import Decimal

import fastapi
from fastapi import Depends, HTTPException
from fastapi.responses import Response

from src.api.dependencies.auth import get_current_user, require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.db.booking import BookingItem
from src.models.schemas.ticket import (
    TicketResponse,
    MarkTicketUsedRequest,
    MarkTicketUsedResponse,
    TransferTicketRequest,
    TransferTicketResponse,
    ClaimTransferRequest,
    ClaimTransferResponse,
    CancelTransferResponse,
    TransferHistoryItem,
    TransferHistoryResponse,
)
from src.repository.crud.ticket import TicketCRUDRepository
from src.repository.crud.booking import BookingCRUDRepository
from src.services.ticket_service import ticket_service
from src.utilities.exceptions.database import EntityDoesNotExist

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/tickets", tags=["tickets"])


# Helper function to convert a BookingItem database model into a TicketResponse schema.
# Extracts event and venue details from the related booking/event/venue chain.
def _build_ticket_response(ticket: BookingItem) -> TicketResponse:
    """Build a TicketResponse from a BookingItem."""
    event = ticket.booking.event
    venue_name = None
    venue_city = None
    # Safely access nested venue properties which may be null
    if event and event.venue:
        venue_name = event.venue.name
        venue_city = event.venue.city

    return TicketResponse(
        id=ticket.id,
        booking_id=ticket.booking_id,
        ticket_number=ticket.ticket_number,
        category_name=ticket.category_name,
        seat_label=ticket.seat_label,
        price=Decimal(str(ticket.price)),
        is_used=ticket.is_used,
        used_at=ticket.used_at,
        created_at=ticket.created_at,
        event_id=ticket.booking.event_id,
        event_title=event.title if event else "Unknown Event",
        event_date=event.event_date if event else None,
        venue_name=venue_name,
        venue_city=venue_city,
        booking_number=ticket.booking.booking_number,
        booking_status=ticket.booking.status,
    )


# --- GET /tickets/{ticket_id} ---
# Returns full ticket details for a single ticket.
# Only the owner of the associated booking can access this endpoint.
@router.get(
    "/{ticket_id}",
    name="tickets:get-ticket",
    response_model=TicketResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_ticket(
    ticket_id: int,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> TicketResponse:
    """Get ticket details by ID."""
    # Look up the ticket by its primary key
    try:
        ticket = await ticket_repo.read_ticket_by_id(ticket_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Ownership check: the ticket belongs to whoever owns the parent booking
    if ticket.booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _build_ticket_response(ticket)


# --- GET /tickets/{ticket_id}/download ---
# Generates and returns a downloadable PDF for a specific ticket.
# The PDF includes ticket number, event details, venue info, and a QR code.
@router.get(
    "/{ticket_id}/download",
    name="tickets:download-ticket",
    status_code=fastapi.status.HTTP_200_OK,
)
async def download_ticket_pdf(
    ticket_id: int,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> Response:
    """Download ticket as PDF."""
    # Fetch the ticket record from the database
    try:
        ticket = await ticket_repo.read_ticket_by_id(ticket_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Only the booking owner can download this ticket
    if ticket.booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Gather event and venue data needed for the PDF layout
    event = ticket.booking.event
    venue_name = None
    venue_address = None
    if event and event.venue:
        venue_name = event.venue.name
        # Combine address and city into a single display string
        if event.venue.address:
            venue_address = f"{event.venue.address}, {event.venue.city or ''}"

    # Prepare structured data dictionaries for the PDF generator
    ticket_data = {
        "ticket_number": ticket.ticket_number,
        "category_name": ticket.category_name,
        "seat_label": ticket.seat_label,
        "price": float(ticket.price),
    }

    event_data = {
        "title": event.title if event else "Event",
        "event_date": str(event.event_date) if event else None,
        "venue_name": venue_name,
        "venue_address": venue_address,
    }

    booking_data = {
        "booking_number": ticket.booking.booking_number,
        "contact_email": ticket.booking.contact_email or ticket.booking.user.email,
    }

    # Generate the PDF bytes using the ticket service
    pdf_bytes = ticket_service.generate_ticket_pdf(
        ticket_data=ticket_data,
        event_data=event_data,
        booking_data=booking_data,
    )

    # Return the PDF as a downloadable attachment with a descriptive filename
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=ticket-{ticket.ticket_number}.pdf"
        }
    )


# --- POST /tickets/mark-used ---
# Admin-only endpoint for marking a ticket as used at event entry (e.g., after QR scan).
# Prevents re-entry by flagging the ticket with a usage timestamp.
@router.post(
    "/mark-used",
    name="tickets:mark-ticket-used",
    response_model=MarkTicketUsedResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def mark_ticket_used(
    request: MarkTicketUsedRequest,
    current_user: Account = Depends(require_admin),  # Admin only
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> MarkTicketUsedResponse:
    """
    Mark a ticket as used (for organizers/admins).
    This should be called after validating a ticket at event entry.
    """
    try:
        # Attempt to mark the ticket; raises ValueError if already used
        ticket = await ticket_repo.mark_ticket_used(request.ticket_number)
        return MarkTicketUsedResponse(
            success=True,
            ticket_number=ticket.ticket_number,
            message="Ticket marked as used",
            used_at=ticket.used_at,
        )
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except ValueError as e:
        # Raised when the ticket has already been used or is otherwise invalid
        raise HTTPException(status_code=400, detail=str(e))


# --- POST /tickets/{ticket_id}/transfer ---
# Initiates a ticket transfer from the current owner to another user identified by email.
# Creates a transfer record with a token that the recipient uses to claim the ticket.
@router.post(
    "/{ticket_id}/transfer",
    name="tickets:transfer-ticket",
    response_model=TransferTicketResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def transfer_ticket(
    ticket_id: int,
    request: TransferTicketRequest,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> TransferTicketResponse:
    """Initiate a ticket transfer to another user."""
    try:
        # Create a pending transfer with an expiration window
        transfer = await ticket_repo.initiate_transfer(
            ticket_id=ticket_id,
            from_user_id=current_user.id,
            to_email=request.to_email,
            message=request.message,
        )

        # TODO: Send email notification to recipient with transfer_token

        return TransferTicketResponse(
            success=True,
            transfer_id=transfer.id,
            message=f"Transfer initiated. The recipient will receive an email at {request.to_email}",
            expires_at=transfer.expires_at,
        )
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except ValueError as e:
        # Raised for business rule violations (e.g., ticket already transferred, used, etc.)
        raise HTTPException(status_code=400, detail=str(e))


# --- POST /tickets/claim ---
# Allows a user to claim a ticket that was transferred to them using a transfer token.
# The token is typically received via email and ties the transfer to the recipient.
@router.post(
    "/claim",
    name="tickets:claim-transfer",
    response_model=ClaimTransferResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def claim_transfer(
    request: ClaimTransferRequest,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> ClaimTransferResponse:
    """Claim a transferred ticket."""
    # Validate the transfer token, check expiration, and reassign ownership
    success, message, ticket = await ticket_repo.claim_transfer(
        transfer_token=request.transfer_token,
        user_id=current_user.id,
        user_email=current_user.email,
    )

    return ClaimTransferResponse(
        success=success,
        ticket_number=ticket.ticket_number if ticket else None,
        message=message,
    )


# --- POST /tickets/transfers/{transfer_id}/cancel ---
# Cancels a pending transfer that has not yet been claimed by the recipient.
# Only the original ticket owner (who initiated the transfer) can cancel it.
@router.post(
    "/transfers/{transfer_id}/cancel",
    name="tickets:cancel-transfer",
    response_model=CancelTransferResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def cancel_transfer(
    transfer_id: int,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> CancelTransferResponse:
    """Cancel a pending ticket transfer."""
    try:
        # Cancel the transfer; verifies the current user is the original sender
        await ticket_repo.cancel_transfer(transfer_id, current_user.id)
        return CancelTransferResponse(
            success=True,
            message="Transfer cancelled successfully",
        )
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Transfer not found")
    except ValueError as e:
        # Raised if the transfer is already claimed, expired, or cancelled
        raise HTTPException(status_code=400, detail=str(e))


# --- GET /tickets/transfers/history ---
# Returns a paginated list of all ticket transfers involving the current user,
# both as sender and receiver, sorted by creation date.
@router.get(
    "/transfers/history",
    name="tickets:transfer-history",
    response_model=TransferHistoryResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_transfer_history(
    page: int = 1,
    page_size: int = 20,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
) -> TransferHistoryResponse:
    """Get ticket transfer history for the current user."""
    # Fetch paginated transfer records for the authenticated user
    transfers, total = await ticket_repo.read_transfer_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    # Map each transfer record into a response schema with ticket and user details
    return TransferHistoryResponse(
        transfers=[
            TransferHistoryItem(
                id=t.id,
                ticket_number=t.booking_item.ticket_number,
                from_email=t.from_user.email,
                to_email=t.to_email,
                status=t.status,
                message=t.message,
                created_at=t.created_at,
                transferred_at=t.transferred_at,
                expires_at=t.expires_at,
            )
            for t in transfers
        ],
        total=total,
    )


# --- GET /tickets/booking/{booking_id} ---
# Returns all tickets associated with a specific booking.
# Accessible by the booking owner or an admin user.
# Booking-specific ticket endpoints
@router.get(
    "/booking/{booking_id}",
    name="tickets:get-booking-tickets",
    response_model=list[TicketResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_booking_tickets(
    booking_id: int,
    current_user: Account = Depends(get_current_user),
    ticket_repo: TicketCRUDRepository = Depends(get_repository(repo_type=TicketCRUDRepository)),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> list[TicketResponse]:
    """Get all tickets for a booking."""
    # Verify booking ownership or admin access
    try:
        booking = await booking_repo.read_booking_by_id(booking_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Allow access if user owns the booking OR is an admin
    if booking.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch all ticket (BookingItem) records for this booking
    tickets = await ticket_repo.read_tickets_by_booking(booking_id)

    # Convert each ticket into a response schema
    return [_build_ticket_response(t) for t in tickets]
