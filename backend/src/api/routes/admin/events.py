"""
Admin Event Management APIs
"""
# Admin event management routes -- provides full CRUD for events and their seat
# categories. Includes lifecycle management (publish, cancel, reactivate) and
# audit logging for every mutating action. All endpoints require admin authentication.

import datetime
from typing import Annotated

import fastapi
from fastapi import Query, Request

from src.api.dependencies.repository import get_repository
from src.api.dependencies.auth import require_admin
from src.models.db.account import Account
from src.models.db.event import EventStatus, EventCategory
from src.models.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventAdminResponse,
    EventListResponse,
    SeatCategoryCreate,
    SeatCategoryUpdate,
    SeatCategoryResponse,
)
from src.models.schemas.venue import VenueCompact
from src.repository.crud.event import EventCRUDRepository
from src.repository.crud.seat_category import SeatCategoryCRUDRepository
from src.repository.crud.seat import SeatCRUDRepository
from src.services.admin_log_service import AdminLogService

router = fastapi.APIRouter(prefix="/events", tags=["admin-events"])


# Helper to convert an Event ORM model into the public-facing EventResponse schema.
# Includes a compact venue representation if the event has an associated venue.
def _build_event_response(event) -> EventResponse:
    """Build EventResponse from Event model"""
    # Build compact venue info if a venue relationship is loaded
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
        # Queue settings
        queue_enabled=event.queue_enabled,
        queue_batch_size=event.queue_batch_size,
        queue_processing_minutes=event.queue_processing_minutes,
    )


# Helper to convert an Event ORM model into the admin-only EventAdminResponse schema.
# This includes all fields from EventResponse plus sensitive/internal fields like
# organizer_contact, terms_and_conditions, metadata, and audit timestamps.
def _build_event_admin_response(event) -> EventAdminResponse:
    """Build EventAdminResponse from Event model"""
    # Build compact venue info if a venue relationship is loaded
    venue = None
    if event.venue:
        venue = VenueCompact(
            id=event.venue.id,
            name=event.venue.name,
            city=event.venue.city,
            state=event.venue.state,
        )

    return EventAdminResponse(
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
        metadata=event.metadata,
        total_seats=event.total_seats,
        available_seats=event.available_seats,
        max_tickets_per_booking=event.max_tickets_per_booking,
        is_booking_open=event.is_booking_open,
        created_at=event.created_at,
        created_by=event.created_by,
        updated_at=event.updated_at,
        published_at=event.published_at,
        cancelled_at=event.cancelled_at,
        # Queue settings
        queue_enabled=event.queue_enabled,
        queue_batch_size=event.queue_batch_size,
        queue_processing_minutes=event.queue_processing_minutes,
    )


# ==================== Event CRUD ====================


# GET /admin/events -- List all events with optional filtering by status,
# category, city, search term, and date range. Admin sees all events
# including drafts and cancelled events (published_only=False).
@router.get(
    "",
    name="admin:events:list",
    response_model=EventListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_events(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status: str | None = None,
    category: str | None = None,
    city: str | None = None,
    search: str | None = None,
    date_from: datetime.date | None = None,
    date_to: datetime.date | None = None,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> EventListResponse:
    """List all events with filters (Admin only - includes draft/cancelled)"""
    # Fetch events with all provided filters; published_only=False lets admin see all statuses
    events, total = await event_repo.read_events(
        page=page,
        page_size=page_size,
        status=status,
        category=category,
        city=city,
        search=search,
        date_from=date_from,
        date_to=date_to,
        published_only=False,  # Admin sees all
    )

    return EventListResponse(
        events=[_build_event_response(event) for event in events],
        total=total,
        page=page,
        page_size=page_size,
    )


# POST /admin/events -- Create a new event. New events are always created
# in draft status. The creating admin's ID is recorded. The action is
# logged to the admin activity audit trail.
@router.post(
    "",
    name="admin:events:create",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_event(
    event_create: EventCreate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> EventAdminResponse:
    """Create a new event (Admin only). Events are created as draft."""
    # Persist the new event with the admin's ID as the creator
    event = await event_repo.create_event(
        event_create=event_create, created_by=admin.id
    )

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="create_event",
        entity_type="event",
        entity_id=event.id,
        details={"event_title": event.title},
        ip_address=request.client.host if request.client else None,
    )

    return _build_event_admin_response(event)


# GET /admin/events/stats -- Returns aggregate event statistics such as
# counts by status, category breakdown, and upcoming event counts.
@router.get(
    "/stats",
    name="admin:events:stats",
    response_model=dict,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event_stats(
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> dict:
    """Get event statistics for admin dashboard"""
    return await event_repo.get_event_stats()


# GET /admin/events/{event_id} -- Retrieve full event details by ID.
# Returns the admin-enriched response including internal fields.
@router.get(
    "/{event_id}",
    name="admin:events:get",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event(
    event_id: int,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
) -> EventAdminResponse:
    """Get event details by ID (Admin only - includes all fields)"""
    event = await event_repo.read_event_by_id(event_id=event_id)
    return _build_event_admin_response(event)


# PATCH /admin/events/{event_id} -- Partially update an event. Only the
# fields provided in the request body are updated (exclude_unset).
# Changes are audit-logged with the specific fields that were modified.
@router.patch(
    "/{event_id}",
    name="admin:events:update",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> EventAdminResponse:
    """Update an event (Admin only)"""
    event = await event_repo.update_event(event_id=event_id, event_update=event_update)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="update_event",
        entity_type="event",
        entity_id=event.id,
        details={"updates": event_update.model_dump(exclude_unset=True)},
        ip_address=request.client.host if request.client else None,
    )

    return _build_event_admin_response(event)


# POST /admin/events/{event_id}/publish -- Transition an event from draft
# to published status, making it visible to end users on the platform.
@router.post(
    "/{event_id}/publish",
    name="admin:events:publish",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def publish_event(
    event_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> EventAdminResponse:
    """Publish an event (make it visible to users)"""
    event = await event_repo.publish_event(event_id=event_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="publish_event",
        entity_type="event",
        entity_id=event.id,
        details={"event_title": event.title},
        ip_address=request.client.host if request.client else None,
    )

    return _build_event_admin_response(event)


# POST /admin/events/{event_id}/cancel -- Cancel an event. This marks the
# event as cancelled, preventing further bookings. Existing bookings may
# need to be handled separately.
@router.post(
    "/{event_id}/cancel",
    name="admin:events:cancel",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def cancel_event(
    event_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> EventAdminResponse:
    """Cancel an event"""
    event = await event_repo.cancel_event(event_id=event_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="cancel_event",
        entity_type="event",
        entity_id=event.id,
        details={"event_title": event.title},
        ip_address=request.client.host if request.client else None,
    )

    return _build_event_admin_response(event)


# POST /admin/events/{event_id}/reactivate -- Reactivate a previously
# cancelled event by moving it back to draft status. The event must be
# published again to become visible to users.
@router.post(
    "/{event_id}/reactivate",
    name="admin:events:reactivate",
    response_model=EventAdminResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def reactivate_event(
    event_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> EventAdminResponse:
    """Reactivate a cancelled event (sets it back to draft status)"""
    event = await event_repo.reactivate_event(event_id=event_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="reactivate_event",
        entity_type="event",
        entity_id=event.id,
        details={"event_title": event.title},
        ip_address=request.client.host if request.client else None,
    )

    return _build_event_admin_response(event)


# DELETE /admin/events/{event_id} -- Permanently delete an event. Only
# draft events can be deleted; published or cancelled events must first
# be handled through their respective lifecycle transitions. The event
# title is captured before deletion for the audit log entry.
@router.delete(
    "/{event_id}",
    name="admin:events:delete",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_event(
    event_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """Delete an event (only draft events can be deleted)"""
    # Get event first for logging
    event = await event_repo.read_event_by_id(event_id=event_id)
    event_title = event.title

    await event_repo.delete_event(event_id=event_id)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="delete_event",
        entity_type="event",
        entity_id=event_id,
        details={"event_title": event_title},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Event '{event_title}' deleted successfully"}


# ==================== Seat Categories ====================


# GET /admin/events/{event_id}/categories -- List all seat categories
# for a given event. Unlike the public endpoint, this returns inactive
# categories as well (active_only=False).
@router.get(
    "/{event_id}/categories",
    name="admin:events:categories:list",
    response_model=list[SeatCategoryResponse],
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_event_categories(
    event_id: int,
    admin: Account = fastapi.Depends(require_admin),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
) -> list[SeatCategoryResponse]:
    """Get all seat categories for an event (Admin only - includes inactive)"""
    categories = await category_repo.read_categories_by_event(
        event_id=event_id, active_only=False
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


# POST /admin/events/{event_id}/categories -- Create a new seat category
# for an event (e.g. VIP, General Admission). After creation, the event's
# aggregate seat counts are recalculated to stay in sync.
@router.post(
    "/{event_id}/categories",
    name="admin:events:categories:create",
    response_model=SeatCategoryResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def create_event_category(
    event_id: int,
    category_create: SeatCategoryCreate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatCategoryResponse:
    """Create a new seat category for an event"""
    # Verify event exists
    event = await event_repo.read_event_by_id(event_id=event_id)

    # Persist the new seat category linked to this event
    category = await category_repo.create_category(
        event_id=event_id, category_create=category_create
    )

    # Update event seat counts -- recalculate totals from all categories
    # so the event's total_seats and available_seats stay accurate
    total_seats, available_seats = await category_repo.get_total_seats_for_event(event_id)
    await event_repo.update_seat_counts(event_id, total_seats, available_seats)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="create_seat_category",
        entity_type="seat_category",
        entity_id=category.id,
        details={
            "event_id": event_id,
            "category_name": category.name,
            "total_seats": category.total_seats,
        },
        ip_address=request.client.host if request.client else None,
    )

    return SeatCategoryResponse(
        id=category.id,
        event_id=category.event_id,
        name=category.name,
        description=category.description,
        price=category.price,
        total_seats=category.total_seats,
        available_seats=category.available_seats,
        display_order=category.display_order,
        color_code=category.color_code,
        is_active=category.is_active,
        created_at=category.created_at,
    )


# PATCH /admin/events/categories/{category_id} -- Partially update a seat
# category. If total_seats is changed, the parent event's aggregate seat
# counts are recalculated to maintain consistency.
@router.patch(
    "/categories/{category_id}",
    name="admin:events:categories:update",
    response_model=SeatCategoryResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_category(
    category_id: int,
    category_update: SeatCategoryUpdate,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> SeatCategoryResponse:
    """Update a seat category"""
    category = await category_repo.update_category(
        category_id=category_id, category_update=category_update
    )

    # Update event seat counts if total_seats changed
    if category_update.total_seats is not None:
        total_seats, available_seats = await category_repo.get_total_seats_for_event(
            category.event_id
        )
        await event_repo.update_seat_counts(category.event_id, total_seats, available_seats)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="update_seat_category",
        entity_type="seat_category",
        entity_id=category.id,
        details={"updates": category_update.model_dump(exclude_unset=True)},
        ip_address=request.client.host if request.client else None,
    )

    return SeatCategoryResponse(
        id=category.id,
        event_id=category.event_id,
        name=category.name,
        description=category.description,
        price=category.price,
        total_seats=category.total_seats,
        available_seats=category.available_seats,
        display_order=category.display_order,
        color_code=category.color_code,
        is_active=category.is_active,
        created_at=category.created_at,
    )


# DELETE /admin/events/categories/{category_id} -- Delete a seat category.
# Only allowed if no seats in this category have been sold. After deletion,
# the parent event's aggregate seat counts are recalculated.
@router.delete(
    "/categories/{category_id}",
    name="admin:events:categories:delete",
    status_code=fastapi.status.HTTP_200_OK,
)
async def delete_category(
    category_id: int,
    request: Request,
    admin: Account = fastapi.Depends(require_admin),
    event_repo: EventCRUDRepository = fastapi.Depends(
        get_repository(repo_type=EventCRUDRepository)
    ),
    category_repo: SeatCategoryCRUDRepository = fastapi.Depends(
        get_repository(repo_type=SeatCategoryCRUDRepository)
    ),
    log_service: AdminLogService = fastapi.Depends(
        get_repository(repo_type=AdminLogService)
    ),
) -> dict:
    """Delete a seat category (only if no seats sold)"""
    # Get category first for logging
    category = await category_repo.read_category_by_id(category_id=category_id)
    event_id = category.event_id
    category_name = category.name

    await category_repo.delete_category(category_id=category_id)

    # Update event seat counts
    total_seats, available_seats = await category_repo.get_total_seats_for_event(event_id)
    await event_repo.update_seat_counts(event_id, total_seats, available_seats)

    # Log admin action
    await log_service.log_action(
        admin_id=admin.id,
        action="delete_seat_category",
        entity_type="seat_category",
        entity_id=category_id,
        details={"event_id": event_id, "category_name": category_name},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Category '{category_name}' deleted successfully"}
