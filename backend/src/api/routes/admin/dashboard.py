import logging
from datetime import datetime, timedelta
from typing import Optional

import fastapi
from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, and_

from src.api.dependencies.auth import require_admin
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.db.booking import Booking
from src.models.db.event import Event
from src.models.db.payment import Payment
from src.repository.crud.base import BaseCRUDRepository

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


class DashboardOverviewResponse(BaseModel):
    total_users: int
    new_users_today: int
    new_users_week: int
    new_users_month: int
    total_events: int
    active_events: int
    completed_events: int
    upcoming_events: int
    total_bookings: int
    bookings_today: int
    bookings_week: int
    bookings_month: int
    total_revenue: float
    revenue_today: float
    revenue_week: float
    revenue_month: float
    total_tickets_sold: int
    tickets_sold_today: int
    tickets_sold_week: int
    revenue_growth_percent: float = 0
    bookings_growth_percent: float = 0
    users_growth_percent: float = 0


class RevenueDataPoint(BaseModel):
    date: str
    revenue: float
    bookings: int


class RevenueChartData(BaseModel):
    data: list[RevenueDataPoint]


class RecentActivityItem(BaseModel):
    type: str
    title: str
    description: str
    timestamp: datetime
    metadata: Optional[dict] = None


class DashboardResponse(BaseModel):
    overview: DashboardOverviewResponse
    revenue_chart: RevenueChartData
    recent_bookings: list[dict]
    upcoming_events: list[dict]


@router.get(
    "/overview",
    name="admin:dashboard-overview",
    response_model=DashboardOverviewResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_dashboard_overview(
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> DashboardOverviewResponse:
    """Get dashboard overview statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)
    prev_month_start = month_start - timedelta(days=30)

    # User stats
    total_users_result = await repo.async_session.execute(
        select(func.count(Account.id))
    )
    total_users = total_users_result.scalar() or 0

    new_users_today_result = await repo.async_session.execute(
        select(func.count(Account.id)).where(Account.created_at >= today_start)
    )
    new_users_today = new_users_today_result.scalar() or 0

    new_users_week_result = await repo.async_session.execute(
        select(func.count(Account.id)).where(Account.created_at >= week_start)
    )
    new_users_week = new_users_week_result.scalar() or 0

    new_users_month_result = await repo.async_session.execute(
        select(func.count(Account.id)).where(Account.created_at >= month_start)
    )
    new_users_month = new_users_month_result.scalar() or 0

    # Event stats
    total_events_result = await repo.async_session.execute(
        select(func.count(Event.id))
    )
    total_events = total_events_result.scalar() or 0

    active_events_result = await repo.async_session.execute(
        select(func.count(Event.id)).where(Event.status == "published")
    )
    active_events = active_events_result.scalar() or 0

    upcoming_events_result = await repo.async_session.execute(
        select(func.count(Event.id)).where(
            and_(Event.status == "published", Event.event_date > now)
        )
    )
    upcoming_events = upcoming_events_result.scalar() or 0

    completed_events_result = await repo.async_session.execute(
        select(func.count(Event.id)).where(Event.status == "completed")
    )
    completed_events = completed_events_result.scalar() or 0

    # Booking stats
    confirmed_filter = Booking.status == "confirmed"

    total_bookings_result = await repo.async_session.execute(
        select(func.count(Booking.id)).where(confirmed_filter)
    )
    total_bookings = total_bookings_result.scalar() or 0

    bookings_today_result = await repo.async_session.execute(
        select(func.count(Booking.id)).where(
            and_(confirmed_filter, Booking.created_at >= today_start)
        )
    )
    bookings_today = bookings_today_result.scalar() or 0

    bookings_week_result = await repo.async_session.execute(
        select(func.count(Booking.id)).where(
            and_(confirmed_filter, Booking.created_at >= week_start)
        )
    )
    bookings_week = bookings_week_result.scalar() or 0

    bookings_month_result = await repo.async_session.execute(
        select(func.count(Booking.id)).where(
            and_(confirmed_filter, Booking.created_at >= month_start)
        )
    )
    bookings_month = bookings_month_result.scalar() or 0

    # Revenue stats
    total_revenue_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(confirmed_filter)
    )
    total_revenue = float(total_revenue_result.scalar() or 0)

    revenue_today_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(
            and_(confirmed_filter, Booking.created_at >= today_start)
        )
    )
    revenue_today = float(revenue_today_result.scalar() or 0)

    revenue_week_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(
            and_(confirmed_filter, Booking.created_at >= week_start)
        )
    )
    revenue_week = float(revenue_week_result.scalar() or 0)

    revenue_month_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(
            and_(confirmed_filter, Booking.created_at >= month_start)
        )
    )
    revenue_month = float(revenue_month_result.scalar() or 0)

    # Previous month revenue for growth calculation
    prev_month_revenue_result = await repo.async_session.execute(
        select(func.sum(Booking.final_amount)).where(
            and_(
                confirmed_filter,
                Booking.created_at >= prev_month_start,
                Booking.created_at < month_start,
            )
        )
    )
    prev_month_revenue = float(prev_month_revenue_result.scalar() or 0)

    # Calculate growth percentages
    revenue_growth_percent = 0.0
    if prev_month_revenue > 0:
        revenue_growth_percent = ((revenue_month - prev_month_revenue) / prev_month_revenue) * 100

    # Tickets stats
    total_tickets_result = await repo.async_session.execute(
        select(func.sum(Booking.ticket_count)).where(confirmed_filter)
    )
    total_tickets = total_tickets_result.scalar() or 0

    tickets_today_result = await repo.async_session.execute(
        select(func.sum(Booking.ticket_count)).where(
            and_(confirmed_filter, Booking.created_at >= today_start)
        )
    )
    tickets_today = tickets_today_result.scalar() or 0

    tickets_week_result = await repo.async_session.execute(
        select(func.sum(Booking.ticket_count)).where(
            and_(confirmed_filter, Booking.created_at >= week_start)
        )
    )
    tickets_week = tickets_week_result.scalar() or 0

    return DashboardOverviewResponse(
        total_users=total_users,
        new_users_today=new_users_today,
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        total_events=total_events,
        active_events=active_events,
        completed_events=completed_events,
        upcoming_events=upcoming_events,
        total_bookings=total_bookings,
        bookings_today=bookings_today,
        bookings_week=bookings_week,
        bookings_month=bookings_month,
        total_revenue=total_revenue,
        revenue_today=revenue_today,
        revenue_week=revenue_week,
        revenue_month=revenue_month,
        total_tickets_sold=total_tickets,
        tickets_sold_today=tickets_today,
        tickets_sold_week=tickets_week,
        revenue_growth_percent=revenue_growth_percent,
        bookings_growth_percent=0,
        users_growth_percent=0,
    )


@router.get(
    "/revenue-chart",
    name="admin:revenue-chart",
    response_model=RevenueChartData,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_revenue_chart(
    period: str = Query("week", pattern="^(week|month|quarter)$"),
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> RevenueChartData:
    """Get revenue chart data for a period."""
    now = datetime.utcnow()

    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:  # quarter
        days = 90

    start_date = now - timedelta(days=days)

    result = await repo.async_session.execute(
        select(
            func.date(Booking.created_at).label("date"),
            func.sum(Booking.final_amount).label("revenue"),
            func.count(Booking.id).label("bookings"),
        )
        .where(
            and_(
                Booking.status == "confirmed",
                Booking.created_at >= start_date,
            )
        )
        .group_by(func.date(Booking.created_at))
        .order_by(func.date(Booking.created_at))
    )

    raw_data = {str(row.date): {"revenue": float(row.revenue or 0), "bookings": row.bookings} for row in result.all()}

    # Fill in missing dates with zeros
    data_points = []
    current_date = start_date.date()
    end_date = now.date()

    while current_date <= end_date:
        date_str = str(current_date)
        if date_str in raw_data:
            data_points.append(RevenueDataPoint(
                date=date_str,
                revenue=raw_data[date_str]["revenue"],
                bookings=raw_data[date_str]["bookings"],
            ))
        else:
            data_points.append(RevenueDataPoint(
                date=date_str,
                revenue=0,
                bookings=0,
            ))
        current_date += timedelta(days=1)

    return RevenueChartData(data=data_points)


@router.get(
    "/recent-bookings",
    name="admin:recent-bookings",
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_recent_bookings(
    limit: int = Query(10, ge=1, le=50),
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> dict:
    """Get recent bookings for dashboard."""
    from sqlalchemy.orm import selectinload

    result = await repo.async_session.execute(
        select(Booking)
        .options(
            selectinload(Booking.user),
            selectinload(Booking.event),
        )
        .order_by(Booking.created_at.desc())
        .limit(limit)
    )
    bookings = result.scalars().all()

    return {
        "bookings": [
            {
                "id": b.id,
                "booking_number": b.booking_number,
                "user_email": b.user.email,
                "user_name": b.user.full_name or b.user.username,
                "event_title": b.event.title,
                "amount": float(b.final_amount),
                "status": b.status,
                "payment_status": b.payment_status,
                "ticket_count": b.ticket_count,
                "created_at": str(b.created_at),
            }
            for b in bookings
        ]
    }


@router.get(
    "/upcoming-events",
    name="admin:upcoming-events",
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_upcoming_events_dashboard(
    limit: int = Query(5, ge=1, le=20),
    current_admin: Account = Depends(require_admin),
    repo: BaseCRUDRepository = Depends(get_repository(repo_type=BaseCRUDRepository)),
) -> dict:
    """Get upcoming events for dashboard."""
    now = datetime.utcnow()

    result = await repo.async_session.execute(
        select(Event)
        .where(
            and_(
                Event.status == "published",
                Event.event_date > now,
            )
        )
        .order_by(Event.event_date)
        .limit(limit)
    )
    events = result.scalars().all()

    # Get booking counts for each event
    event_stats = {}
    if events:
        event_ids = [e.id for e in events]
        stats_result = await repo.async_session.execute(
            select(
                Booking.event_id,
                func.count(Booking.id).label("bookings"),
                func.sum(Booking.ticket_count).label("tickets"),
            )
            .where(
                and_(
                    Booking.event_id.in_(event_ids),
                    Booking.status == "confirmed",
                )
            )
            .group_by(Booking.event_id)
        )
        for row in stats_result.all():
            event_stats[row.event_id] = {
                "bookings": row.bookings,
                "tickets": row.tickets or 0,
            }

    return {
        "events": [
            {
                "id": e.id,
                "title": e.title,
                "event_date": str(e.event_date),
                "status": e.status,
                "total_seats": e.total_seats,
                "available_seats": e.available_seats,
                "bookings": event_stats.get(e.id, {}).get("bookings", 0),
                "tickets_sold": event_stats.get(e.id, {}).get("tickets", 0),
            }
            for e in events
        ]
    }
