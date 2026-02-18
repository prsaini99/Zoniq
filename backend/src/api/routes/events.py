"""
Public Event APIs - accessible to all users (no authentication required)
"""
import datetime
from typing import Annotated

import fastapi
from fastapi import Query

from src.api.dependencies.repository import get_repository
from src.models.db.event import EventStatus, EventCategory
from src.models.schemas.event import (
    EventResponse,
    EventDetailResponse,
    EventListResponse,
    SeatCategoryResponse,
    EventSeatsResponse,
    SeatAvailabilityResponse,
)
from src.models.schemas.venue import VenueCompact
from src.repository.crud.event import EventCRUDRepository
from src.repository.crud.seat_category import SeatCategoryCRUDRepository
from src.repository.crud.seat import SeatCRUDRepository

router = fastapi.APIRouter(prefix="/events", tags=["events"])


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


def _build_event_detail_response(event) -> EventDetailResponse:
    """Build EventDetailResponse from Event model"""
    venue = None
    if event.venue:
        venue = VenueCompact(
            id=event.venue.id,
            name=event.venue.name,
            city=event.venue.city,
            state=event.venue.state,
        )

    return EventDetailResponse(
        id=event.id,
        title=event.title,
        slug=event.slug,
        short_description=event.short_description,
        description=event.description,
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
        organizer_contact=event.organizer_contact,
        terms_and_conditions=event.terms_and_conditions,
        extra_data=event.extra_data,
        total_seats=event.total_seats,
        available_seats=event.available_seats,
        max_tickets_per_booking=event.max_tickets_per_booking,
        is_booking_open=event.is_booking_open,
        created_at=event.created_at,
        published_at=event.published_at,
        queue_enabled=event.queue_enabled,
        queue_batch_size=event.queue_batch_size,
        queue_processing_minutes=event.queue_processing_minutes,
    )


@router.get(
    "",
    name="events:list",
    response_model=EventListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_events(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    city: str | None = None,
    search: str | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> EventListResponse:
    """
    List all published events with optional filters and full-text search.

    - **search**: Full-text search across title, description, short description, and organizer name.
              Uses PostgreSQL full-text search for fast, relevance-ranked results.
    - **category**: Filter by event category (concert, sports, theater, etc.)
    - **city**: Filter by venue city
    - **date_from**: Events starting from this date
    - **date_to**: Events until this date
    """
    events, total = await event_repo.read_events(
        page=page,
        page_size=page_size,
        category=category,
        city=city,
        search=search,
        date_from=date_from,
        date_to=date_to,
        published_only=True,
    )

    return EventListResponse(
        events=[_build_event_response(event) for event in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/search",
    name="events:search",
    response_model=EventListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def search_events(
    q: Annotated[str, Query(min_length=1, max_length=100, description="Search query")],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> EventListResponse:
    """
    Search events using PostgreSQL full-text search.

    Results are ranked by relevance with title matches weighted highest,
    followed by short description and organizer name, then description.

    - **q**: Search query (required, 1-100 characters)
    """
    events, total = await event_repo.read_events(
        page=page,
        page_size=page_size,
        search=q,
        published_only=True,
    )

    return EventListResponse(
        events=[_build_event_response(event) for event in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/upcoming",
    name="events:upcoming",
    response_model=list[EventResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_upcoming_events(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    category: str | None = None,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> list[EventResponse]:
    """Get upcoming events (published events with future dates)"""
    events = await event_repo.read_upcoming_events(limit=limit, category=category)
    return [_build_event_response(event) for event in events]


@router.get(
    "/categories",
    name="events:categories",
    response_model=list[dict],
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_event_categories() -> list[dict]:
    """Get all available event categories"""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in EventCategory
    ]


@router.get(
    "/{event_id_or_slug}",
    name="events:get",
    response_model=EventDetailResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event(
    event_id_or_slug: str,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> EventDetailResponse:
    """
    Get event details by ID or slug.
    Only returns published events.
    """
    try:
        # Try to parse as integer (ID)
        event_id = int(event_id_or_slug)
        event = await event_repo.read_event_by_id(event_id=event_id)
    except ValueError:
        # Not an integer, treat as slug
        event = await event_repo.read_event_by_slug(slug=event_id_or_slug)

    # Only return published events to public
    if event.status != EventStatus.PUBLISHED.value:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return _build_event_detail_response(event)


@router.get(
    "/{event_id}/categories",
    name="events:categories",
    response_model=list[SeatCategoryResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event_categories(
    event_id: int,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
) -> list[SeatCategoryResponse]:
    """Get seat categories (pricing tiers) for an event"""
    # Verify event exists and is published
    event = await event_repo.read_event_by_id(event_id=event_id)
    if event.status != EventStatus.PUBLISHED.value:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    categories = await category_repo.read_categories_by_event(
        event_id=event_id, active_only=True
    )

    return [
        SeatCategoryResponse(
            id=cat.id,
            event_id=cat.event_id,
            name=cat.name,
            description=cat.description,
            price=cat.price,
            total_seats=cat.total_seats,
            available_seats=cat.available_seats,
            display_order=cat.display_order,
            color_code=cat.color_code,
            is_active=cat.is_active,
            created_at=cat.created_at,
        )
        for cat in categories
    ]


@router.get(
    "/{event_id}/seats",
    name="events:seats",
    response_model=EventSeatsResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event_seats(
    event_id: int,
    category_id: int | None = None,
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
    seat_repo: SeatCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCRUDRepository)
    ),
) -> EventSeatsResponse:
    """
    Get seat availability for an event.
    Returns categories and individual seat status for seat map rendering.
    """
    # Verify event exists and is published
    event = await event_repo.read_event_by_id(event_id=event_id)
    if event.status != EventStatus.PUBLISHED.value:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    # Get categories
    categories = await category_repo.read_categories_by_event(
        event_id=event_id, active_only=True
    )

    # Get seats
    seats = await seat_repo.read_seats_by_event(
        event_id=event_id,
        category_id=category_id,
        include_category=False,
    )

    category_responses = [
        SeatCategoryResponse(
            id=cat.id,
            event_id=cat.event_id,
            name=cat.name,
            description=cat.description,
            price=cat.price,
            total_seats=cat.total_seats,
            available_seats=cat.available_seats,
            display_order=cat.display_order,
            color_code=cat.color_code,
            is_active=cat.is_active,
            created_at=cat.created_at,
        )
        for cat in categories
    ]

    seat_responses = [
        SeatAvailabilityResponse(
            id=seat.id,
            category_id=seat.category_id,
            seat_label=seat.seat_label,
            row_name=seat.row_name,
            section=seat.section,
            status=seat.status if not seat.is_available else "available",
            position_x=seat.position_x,
            position_y=seat.position_y,
        )
        for seat in seats
    ]

    return EventSeatsResponse(
        event_id=event_id,
        categories=category_responses,
        seats=seat_responses,
        total_seats=event.total_seats,
        available_seats=event.available_seats,
    )
