# Wishlist routes: let authenticated users save, remove, list, and check events in their wishlist
"""
Wishlist API Routes
"""
import fastapi

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import get_current_user
from src.models.db.account import Account
from src.models.schemas.wishlist import WishlistItemResponse, WishlistResponse, WishlistCheckResponse
from src.models.schemas.event import EventResponse
from src.models.schemas.venue import VenueCompact
from src.repository.crud.wishlist import WishlistCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists

router = fastapi.APIRouter(prefix="/users/me/wishlist", tags=["wishlist"])


# Helper to convert an Event ORM model into an EventResponse schema.
# Includes a compact venue representation if the event has a linked venue.
def _build_event_response(event) -> EventResponse:
    """Build EventResponse from Event model"""
    venue = None
    if event.venue:
        venue = VenueCompact(
            id=event.venue.id,
            name=event.venue.name,
            city=event.venue.city,
            state=event.venue.state,
        )

    return EventResponse(
        id=event.id,
        title=event.title,
        slug=event.slug,
        short_description=event.short_description,
        category=event.category,
        venue=venue,
        event_date=event.event_date,
        event_end_date=event.event_end_date,
        booking_start_date=event.booking_start_date,
        booking_end_date=event.booking_end_date,
        status=event.status,
        banner_image_url=event.banner_image_url,
        thumbnail_image_url=event.thumbnail_image_url,
        organizer_name=event.organizer_name,
        total_seats=event.total_seats,
        available_seats=event.available_seats,
        max_tickets_per_booking=event.max_tickets_per_booking,
        is_booking_open=event.is_booking_open,
        created_at=event.created_at,
        queue_enabled=event.queue_enabled,
        queue_batch_size=event.queue_batch_size,
        queue_processing_minutes=event.queue_processing_minutes,
    )


# --- GET /users/me/wishlist ---
# Returns all events the authenticated user has added to their wishlist.
# Each item includes full event details and the timestamp when it was wishlisted.
@router.get(
    "",
    name="wishlist:list",
    response_model=WishlistResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_wishlist(
    current_user: Account = fastapi.Depends(get_current_user),
    wishlist_repo: WishlistCRUDRepository = fastapi.Depends(
        get_repository(repo_type=WishlistCRUDRepository)
    ),
) -> WishlistResponse:
    """Get user's wishlist"""
    # Fetch all wishlist items for the current user, eagerly loading related events
    items = await wishlist_repo.get_user_wishlist(account_id=current_user.id)

    # Transform each wishlist database record into a response schema with event details
    response_items = [
        WishlistItemResponse(
            id=item.id,
            event_id=item.event_id,
            event=_build_event_response(item.event),
            created_at=item.created_at,
        )
        for item in items
    ]

    return WishlistResponse(items=response_items, total=len(response_items))


# --- POST /users/me/wishlist/{event_id} ---
# Adds a specific event to the current user's wishlist.
# Returns 400 if the event is already wishlisted, 404 if the event does not exist.
@router.post(
    "/{event_id}",
    name="wishlist:add",
    response_model=WishlistItemResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def add_to_wishlist(
    event_id: int,
    current_user: Account = fastapi.Depends(get_current_user),
    wishlist_repo: WishlistCRUDRepository = fastapi.Depends(
        get_repository(repo_type=WishlistCRUDRepository)
    ),
) -> WishlistItemResponse:
    """Add an event to wishlist"""
    try:
        # Create the wishlist entry linking the user to the event
        item = await wishlist_repo.add_to_wishlist(
            account_id=current_user.id,
            event_id=event_id,
        )
        return WishlistItemResponse(
            id=item.id,
            event_id=item.event_id,
            event=_build_event_response(item.event),
            created_at=item.created_at,
        )
    except EntityAlreadyExists as e:
        # The user has already added this event to their wishlist
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except EntityDoesNotExist as e:
        # The specified event ID does not exist in the database
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# --- DELETE /users/me/wishlist/{event_id} ---
# Removes an event from the current user's wishlist.
# Returns 404 if the event was not in the wishlist.
@router.delete(
    "/{event_id}",
    name="wishlist:remove",
    status_code=fastapi.status.HTTP_200_OK,
)
async def remove_from_wishlist(
    event_id: int,
    current_user: Account = fastapi.Depends(get_current_user),
    wishlist_repo: WishlistCRUDRepository = fastapi.Depends(
        get_repository(repo_type=WishlistCRUDRepository)
    ),
) -> dict:
    """Remove an event from wishlist"""
    try:
        # Delete the wishlist record for this user-event combination
        await wishlist_repo.remove_from_wishlist(
            account_id=current_user.id,
            event_id=event_id,
        )
        return {"message": "Event removed from wishlist"}
    except EntityDoesNotExist as e:
        # The event was not in the user's wishlist to begin with
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# --- GET /users/me/wishlist/{event_id}/check ---
# Quick boolean check to see if a specific event is in the user's wishlist.
# Useful for toggling the wishlist icon state on the frontend event card.
@router.get(
    "/{event_id}/check",
    name="wishlist:check",
    response_model=WishlistCheckResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def check_wishlist(
    event_id: int,
    current_user: Account = fastapi.Depends(get_current_user),
    wishlist_repo: WishlistCRUDRepository = fastapi.Depends(
        get_repository(repo_type=WishlistCRUDRepository)
    ),
) -> WishlistCheckResponse:
    """Check if an event is in user's wishlist"""
    # Perform a lightweight existence check without loading the full record
    is_in = await wishlist_repo.is_in_wishlist(
        account_id=current_user.id,
        event_id=event_id,
    )
    return WishlistCheckResponse(is_in_wishlist=is_in)
