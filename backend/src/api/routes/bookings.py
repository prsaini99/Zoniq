import fastapi
from fastapi import Depends, HTTPException

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.booking import (
    BookingCancel,
    BookingResponse,
    BookingDetailResponse,
    BookingListResponse,
    BookingItemResponse,
    BookingEventInfo,
)
from src.repository.crud.booking import BookingCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist

router = fastapi.APIRouter(tags=["bookings"])


def _build_booking_response(booking, include_items: bool = False):
    """Build a BookingResponse from a Booking model instance."""
    event_info = None
    if booking.event:
        venue_name = None
        venue_city = None
        if booking.event.venue:
            venue_name = booking.event.venue.name
            venue_city = booking.event.venue.city

        event_info = BookingEventInfo(
            id=booking.event.id,
            title=booking.event.title,
            slug=booking.event.slug,
            event_date=booking.event.event_date,
            banner_image_url=booking.event.banner_image_url,
            thumbnail_image_url=booking.event.thumbnail_image_url,
            venue_name=venue_name,
            venue_city=venue_city,
        )

    base = dict(
        id=booking.id,
        booking_number=booking.booking_number,
        user_id=booking.user_id,
        event_id=booking.event_id,
        event=event_info,
        status=booking.status,
        total_amount=booking.total_amount,
        discount_amount=booking.discount_amount,
        final_amount=booking.final_amount,
        payment_status=booking.payment_status,
        promo_code_used=booking.promo_code_used,
        ticket_count=booking.ticket_count,
        contact_email=booking.contact_email,
        contact_phone=booking.contact_phone,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )

    if include_items:
        items = [
            BookingItemResponse(
                id=item.id,
                booking_id=item.booking_id,
                seat_id=item.seat_id,
                category_id=item.category_id,
                category_name=item.category_name,
                seat_label=item.seat_label,
                price=item.price,
                ticket_number=item.ticket_number,
                is_used=item.is_used,
                used_at=item.used_at,
            )
            for item in booking.items
        ]
        return BookingDetailResponse(**base, items=items)

    return BookingResponse(**base)


@router.get(
    "/users/me/bookings",
    name="bookings:list-my-bookings",
    response_model=BookingListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_my_bookings(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> BookingListResponse:
    """Get the current user's bookings with pagination."""
    bookings, total = await booking_repo.read_bookings_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )

    return BookingListResponse(
        bookings=[_build_booking_response(b) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/bookings/{booking_id}",
    name="bookings:get-booking",
    response_model=BookingDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_booking(
    booking_id: int,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> BookingDetailResponse:
    """Get a booking by ID (must be owned by current user)."""
    try:
        booking = await booking_repo.read_booking_by_id(booking_id)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _build_booking_response(booking, include_items=True)


@router.get(
    "/bookings/number/{booking_number}",
    name="bookings:get-booking-by-number",
    response_model=BookingDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_booking_by_number(
    booking_number: str,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> BookingDetailResponse:
    """Get a booking by booking number (must be owned by current user)."""
    try:
        booking = await booking_repo.read_booking_by_number(booking_number)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return _build_booking_response(booking, include_items=True)


@router.post(
    "/bookings/{booking_id}/cancel",
    name="bookings:cancel-booking",
    response_model=BookingDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def cancel_booking(
    booking_id: int,
    cancel_data: BookingCancel | None = None,
    current_user: Account = Depends(get_current_user),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> BookingDetailResponse:
    """Cancel a booking (must be owned by current user)."""
    try:
        booking = await booking_repo.cancel_booking(
            booking_id=booking_id,
            user_id=current_user.id,
        )
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Booking not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_booking_response(booking, include_items=True)
