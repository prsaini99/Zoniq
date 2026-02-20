# Admin booking management routes -- provides endpoints for viewing bookings,
# booking statistics, sales analytics, top-performing events, and attendee
# lists. Performs direct SQLAlchemy queries against Booking, BookingItem,
# Event, and Payment models. All endpoints require admin authentication.

import logging
from datetime import datetime, timedelta
from typing import Optional

import fastapi
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload

from src.api.dependencies.auth import require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.db.booking import Booking, BookingItem
from src.models.db.event import Event
from src.models.db.payment import Payment
from src.repository.crud.base import BaseCRUDRepository

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/bookings", tags=["admin-bookings"])


# ==================== Response Schemas ====================
# These Pydantic models are defined inline rather than in the shared schemas
# module because they are specific to the admin booking views.

# Compact user info embedded in the booking response
class BookingUserInfo(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]

    class Config:
        from_attributes = True


# Compact event info embedded in the booking response
class BookingEventInfo(BaseModel):
    id: int
    title: str
    event_date: datetime

    class Config:
        from_attributes = True


# Full admin booking response with user, event, payment, and promo details
class AdminBookingResponse(BaseModel):
    id: int
    booking_number: str
    user: BookingUserInfo
    event: BookingEventInfo
    status: str
    total_amount: float
    discount_amount: float
    final_amount: float
    payment_status: str
    promo_code_used: Optional[str]
    ticket_count: int
    contact_email: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Paginated wrapper for booking list responses
class BookingListResponse(BaseModel):
    bookings: list[AdminBookingResponse]
    total: int
    page: int
    page_size: int


# Aggregate booking statistics with status breakdown and revenue total
class BookingStatsResponse(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    cancelled_bookings: int
    total_revenue: float
    total_tickets_sold: int


# Sales analytics response with aggregate totals and a per-day breakdown
class SalesAnalyticsResponse(BaseModel):
    period: str
    total_revenue: float
    total_bookings: int
    total_tickets: int
    average_order_value: float
    daily_breakdown: list[dict]


# Wrapper for the top events ranked by revenue
class TopEventsResponse(BaseModel):
    events: list[dict]


# Helper to convert a Booking ORM model (with eager-loaded user and event
# relationships) into the AdminBookingResponse schema.
def _build_booking_response(booking: Booking) -> AdminBookingResponse:
    return AdminBookingResponse(
        id=booking.id,
        booking_number=booking.booking_number,
        user=BookingUserInfo(
            id=booking.user.id,
            username=booking.user.username,
            email=booking.user.email,
            full_name=booking.user.full_name,
        ),
        event=BookingEventInfo(
            id=booking.event.id,
            title=booking.event.title,
            event_date=booking.event.event_date,
        ),
        status=booking.status,
        total_amount=float(booking.total_amount),
        discount_amount=float(booking.discount_amount),
        final_amount=float(booking.final_amount),
        payment_status=booking.payment_status,
        promo_code_used=booking.promo_code_used,
        ticket_count=booking.ticket_count,
        contact_email=booking.contact_email,
        contact_phone=booking.contact_phone,
        created_at=booking.created_at,
    )


# GET /admin/bookings -- Paginated booking list with optional filters for
# status, payment_status, event_id, user_id, booking number search, and
# date range. Eager-loads user and event relationships. Results are ordered
# by creation date descending (newest first).
@router.get(
    "",
    name="admin:list-bookings",
    response_model=BookingListResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    event_id: Optional[int] = None,
    user_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> BookingListResponse:
    """List all bookings with filtering."""
    # Base query with eager-loaded relationships for user and event
    stmt = select(Booking).options(
        selectinload(Booking.user),
        selectinload(Booking.event),
    )

    # Apply optional filters -- each narrows the result set
    if status:
        stmt = stmt.where(Booking.status == status)
    if payment_status:
        stmt = stmt.where(Booking.payment_status == payment_status)
    if event_id:
        stmt = stmt.where(Booking.event_id == event_id)
    if user_id:
        stmt = stmt.where(Booking.user_id == user_id)
    if search:
        stmt = stmt.where(Booking.booking_number.ilike(f"%{search}%"))
    if date_from:
        stmt = stmt.where(Booking.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Booking.created_at <= date_to)

    # Count total matching records before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await repo.async_session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination
    stmt = stmt.order_by(Booking.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await repo.async_session.execute(stmt)
    bookings = result.scalars().all()

    return BookingListResponse(
        bookings=[_build_booking_response(b) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
    )


# GET /admin/bookings/stats -- Returns aggregate booking statistics.
# Optionally filtered by event_id. Revenue and tickets sold are counted
# only for confirmed bookings.
@router.get(
    "/stats",
    name="admin:booking-stats",
    response_model=BookingStatsResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_booking_stats(
    event_id: Optional[int] = None,
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> BookingStatsResponse:
    """Get booking statistics."""
    # Conditionally filter by event_id; True means no filter
    base_filter = Booking.event_id == event_id if event_id else True

    # Total bookings
    total_result = await repo.async_session.execute(
        select(func.count(Booking.id)).where(base_filter)
    )
    total_bookings = total_result.scalar() or 0

    # Status counts -- group bookings by status to get confirmed/pending/cancelled counts
    status_result = await repo.async_session.execute(
        select(
            Booking.status,
            func.count(Booking.id),
        )
        .where(base_filter)
        .group_by(Booking.status)
    )
    status_counts = {row[0]: row[1] for row in status_result.all()}

    # Total revenue (confirmed bookings only)
    revenue_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(
            and_(base_filter, Booking.status == "confirmed")
        )
    )
    total_revenue = float(revenue_result.scalar() or 0)

    # Total tickets sold (confirmed bookings only)
    tickets_result = await repo.async_session.execute(
        select(func.sum(Booking.ticket_count)).where(
            and_(base_filter, Booking.status == "confirmed")
        )
    )
    total_tickets = tickets_result.scalar() or 0

    return BookingStatsResponse(
        total_bookings=total_bookings,
        confirmed_bookings=status_counts.get("confirmed", 0),
        pending_bookings=status_counts.get("pending", 0),
        cancelled_bookings=status_counts.get("cancelled", 0),
        total_revenue=total_revenue,
        total_tickets_sold=total_tickets,
    )


# GET /admin/bookings/analytics -- Sales analytics over a configurable
# time period (7d, 30d, 90d, 1y). Only confirmed bookings are counted.
# Returns aggregate totals plus a day-by-day revenue/bookings/tickets
# breakdown for charting.
@router.get(
    "/analytics",
    name="admin:sales-analytics",
    response_model=SalesAnalyticsResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_sales_analytics(
    period: str = Query("7d", pattern="^(7d|30d|90d|1y)$"),
    event_id: Optional[int] = None,
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> SalesAnalyticsResponse:
    """Get sales analytics for a period."""
    # Calculate date range based on the selected period
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    else:  # 1y
        start_date = now - timedelta(days=365)

    # Build filter: confirmed bookings within the date range
    base_filter = and_(
        Booking.created_at >= start_date,
        Booking.status == "confirmed",
    )
    if event_id:
        base_filter = and_(base_filter, Booking.event_id == event_id)

    # Aggregate stats: total revenue, booking count, ticket count
    stats_result = await repo.async_session.execute(
        select(
            func.sum(Booking.final_amount),
            func.count(Booking.id),
            func.sum(Booking.ticket_count),
        ).where(base_filter)
    )
    stats = stats_result.one()
    total_revenue = float(stats[0] or 0)
    total_bookings = stats[1] or 0
    total_tickets = stats[2] or 0
    # Compute average order value, guarding against division by zero
    avg_order_value = total_revenue / total_bookings if total_bookings > 0 else 0

    # Daily breakdown -- group by date for time-series chart data
    daily_result = await repo.async_session.execute(
        select(
            func.date(Booking.created_at).label("date"),
            func.sum(Booking.final_amount).label("revenue"),
            func.count(Booking.id).label("bookings"),
            func.sum(Booking.ticket_count).label("tickets"),
        )
        .where(base_filter)
        .group_by(func.date(Booking.created_at))
        .order_by(func.date(Booking.created_at))
    )
    daily_breakdown = [
        {
            "date": str(row.date),
            "revenue": float(row.revenue or 0),
            "bookings": row.bookings,
            "tickets": row.tickets,
        }
        for row in daily_result.all()
    ]

    return SalesAnalyticsResponse(
        period=period,
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        total_tickets=total_tickets,
        average_order_value=avg_order_value,
        daily_breakdown=daily_breakdown,
    )


# GET /admin/bookings/top-events -- Rank events by total confirmed revenue
# within a configurable time period. Joins Booking to Event and aggregates
# revenue, booking count, and ticket count per event.
@router.get(
    "/top-events",
    name="admin:top-events",
    response_model=TopEventsResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_top_events(
    limit: int = Query(10, ge=1, le=50),
    period: str = Query("30d", pattern="^(7d|30d|90d|1y|all)$"),
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> TopEventsResponse:
    """Get top performing events by revenue."""
    now = datetime.utcnow()
    # Only include confirmed bookings in the ranking
    base_filter = Booking.status == "confirmed"

    # Apply date range filter unless "all" is selected
    if period != "all":
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        else:  # 1y
            start_date = now - timedelta(days=365)
        base_filter = and_(base_filter, Booking.created_at >= start_date)

    # Aggregate revenue, bookings, and tickets per event, ordered by revenue desc
    result = await repo.async_session.execute(
        select(
            Event.id,
            Event.title,
            Event.event_date,
            func.sum(Booking.final_amount).label("revenue"),
            func.count(Booking.id).label("bookings"),
            func.sum(Booking.ticket_count).label("tickets"),
        )
        .join(Event, Booking.event_id == Event.id)
        .where(base_filter)
        .group_by(Event.id, Event.title, Event.event_date)
        .order_by(func.sum(Booking.final_amount).desc())
        .limit(limit)
    )

    events = [
        {
            "id": row.id,
            "title": row.title,
            "event_date": str(row.event_date),
            "revenue": float(row.revenue or 0),
            "bookings": row.bookings,
            "tickets": row.tickets,
        }
        for row in result.all()
    ]

    return TopEventsResponse(events=events)


# GET /admin/bookings/{booking_id} -- Retrieve a single booking by its
# numeric ID. Eager-loads user and event relationships. Returns 404
# if the booking does not exist.
@router.get(
    "/{booking_id}",
    name="admin:get-booking",
    response_model=AdminBookingResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_booking(
    booking_id: int,
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> AdminBookingResponse:
    """Get a specific booking."""
    result = await repo.async_session.execute(
        select(Booking)
        .options(
            selectinload(Booking.user),
            selectinload(Booking.event),
        )
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return _build_booking_response(booking)


# GET /admin/bookings/event/{event_id}/attendees -- Retrieve a paginated
# attendee list for a specific event. Pulls data from BookingItem (individual
# tickets) joined with Booking (for user info). Only includes tickets from
# confirmed bookings. Supports search by ticket number. Also returns a
# checked_in count (tickets where is_used=True).
@router.get(
    "/event/{event_id}/attendees",
    name="admin:event-attendees",
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_event_attendees(
    event_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> dict:
    """Get attendee list for an event."""
    # Query individual booking items (tickets) for confirmed bookings of this event
    stmt = (
        select(BookingItem)
        .join(Booking, BookingItem.booking_id == Booking.id)
        .options(
            selectinload(BookingItem.booking).selectinload(Booking.user),
        )
        .where(
            and_(
                Booking.event_id == event_id,
                Booking.status == "confirmed",
            )
        )
    )

    # Optionally filter by ticket number search
    if search:
        stmt = stmt.where(
            BookingItem.ticket_number.ilike(f"%{search}%")
        )

    # Count total matching tickets before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await repo.async_session.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination ordered by ticket number
    stmt = stmt.order_by(BookingItem.ticket_number)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await repo.async_session.execute(stmt)
    items = result.scalars().all()

    # Build attendee list with ticket details, user info, and check-in status
    attendees = [
        {
            "ticket_id": item.id,
            "ticket_number": item.ticket_number,
            "category_name": item.category_name,
            "seat_label": item.seat_label,
            "is_used": item.is_used,
            "used_at": str(item.used_at) if item.used_at else None,
            "user": {
                "id": item.booking.user.id,
                "username": item.booking.user.username,
                "email": item.booking.user.email,
                "full_name": item.booking.user.full_name,
            },
            "booking_number": item.booking.booking_number,
        }
        for item in items
    ]

    return {
        "attendees": attendees,
        "total": total,
        "page": page,
        "page_size": page_size,
        # Count how many attendees on this page have already checked in
        "checked_in": sum(1 for a in attendees if a["is_used"]),
    }
