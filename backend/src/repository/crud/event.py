import datetime
import typing

import sqlalchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import functions as sqlalchemy_functions
from sqlalchemy import func
from slugify import slugify

from src.models.db.event import Event, EventStatus
from src.models.db.venue import Venue
from src.models.schemas.event import EventCreate, EventUpdate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists


class EventCRUDRepository(BaseCRUDRepository):

    async def _generate_unique_slug(self, title: str, exclude_id: int | None = None) -> str:
        """Generate a unique slug for the event"""
        base_slug = slugify(title, max_length=250)
        slug = base_slug
        counter = 1

        while True:
            stmt = sqlalchemy.select(Event.id).where(Event.slug == slug)
            if exclude_id:
                stmt = stmt.where(Event.id != exclude_id)
            result = await self.async_session.execute(statement=stmt)
            if not result.scalar():
                return slug
            slug = f"{base_slug}-{counter}"
            counter += 1

    async def create_event(self, event_create: EventCreate, created_by: int | None = None) -> Event:
        """Create a new event"""
        slug = await self._generate_unique_slug(event_create.title)

        new_event = Event(
            title=event_create.title,
            slug=slug,
            description=event_create.description,
            short_description=event_create.short_description,
            category=event_create.category,
            venue_id=event_create.venue_id,
            event_date=event_create.event_date,
            event_end_date=event_create.event_end_date,
            booking_start_date=event_create.booking_start_date,
            booking_end_date=event_create.booking_end_date,
            banner_image_url=event_create.banner_image_url,
            thumbnail_image_url=event_create.thumbnail_image_url,
            terms_and_conditions=event_create.terms_and_conditions,
            organizer_name=event_create.organizer_name,
            organizer_contact=event_create.organizer_contact,
            max_tickets_per_booking=event_create.max_tickets_per_booking,
            extra_data=event_create.extra_data,
            created_by=created_by,
            status=EventStatus.DRAFT.value,
        )

        self.async_session.add(instance=new_event)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_event)

        return new_event

    async def read_event_by_id(self, event_id: int, include_venue: bool = True) -> Event:
        """Get an event by ID"""
        stmt = sqlalchemy.select(Event).where(Event.id == event_id)
        if include_venue:
            stmt = stmt.options(joinedload(Event.venue))

        query = await self.async_session.execute(statement=stmt)
        event = query.scalar()

        if not event:
            raise EntityDoesNotExist(f"Event with id '{event_id}' does not exist!")

        return event

    async def read_event_by_slug(self, slug: str, include_venue: bool = True) -> Event:
        """Get an event by slug"""
        stmt = sqlalchemy.select(Event).where(Event.slug == slug)
        if include_venue:
            stmt = stmt.options(joinedload(Event.venue))

        query = await self.async_session.execute(statement=stmt)
        event = query.scalar()

        if not event:
            raise EntityDoesNotExist(f"Event with slug '{slug}' does not exist!")

        return event

    async def read_events(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        category: str | None = None,
        city: str | None = None,
        search: str | None = None,
        date_from: datetime.date | None = None,
        date_to: datetime.date | None = None,
        published_only: bool = False,
        include_venue: bool = True,
    ) -> tuple[typing.Sequence[Event], int]:
        """Get events with pagination and filtering"""
        stmt = sqlalchemy.select(Event)

        if include_venue:
            stmt = stmt.options(joinedload(Event.venue))

        # Apply filters
        if published_only:
            stmt = stmt.where(Event.status == EventStatus.PUBLISHED.value)
        elif status:
            stmt = stmt.where(Event.status == status)

        if category:
            stmt = stmt.where(Event.category == category)

        if city:
            stmt = stmt.join(Venue, Event.venue_id == Venue.id).where(
                Venue.city.ilike(f"%{city}%")
            )

        # Full-text search with ILIKE fallback
        if search:
            search_pattern = f"%{search}%"
            # Use OR to combine full-text search with ILIKE fallback
            # This handles cases where search_vector is null or partial word matches
            search_query = func.plainto_tsquery('english', search)
            stmt = stmt.where(
                sqlalchemy.or_(
                    Event.search_vector.op('@@')(search_query),
                    Event.title.ilike(search_pattern),
                    Event.short_description.ilike(search_pattern),
                    Event.organizer_name.ilike(search_pattern),
                )
            )

        if date_from:
            stmt = stmt.where(Event.event_date >= datetime.datetime.combine(date_from, datetime.time.min))

        if date_to:
            stmt = stmt.where(Event.event_date <= datetime.datetime.combine(date_to, datetime.time.max))

        # Count total
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(stmt.subquery())
        count_result = await self.async_session.execute(statement=count_stmt)
        total = count_result.scalar() or 0

        # Order by relevance when searching, otherwise by event date
        if search:
            search_query = func.plainto_tsquery('english', search)
            stmt = stmt.order_by(
                func.ts_rank(Event.search_vector, search_query).desc(),
                Event.event_date.asc()
            )
        else:
            stmt = stmt.order_by(Event.event_date.asc())

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        query = await self.async_session.execute(statement=stmt)
        events = query.scalars().unique().all()

        return events, total

    async def read_upcoming_events(
        self,
        limit: int = 10,
        category: str | None = None,
    ) -> typing.Sequence[Event]:
        """Get upcoming published events"""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.select(Event)
            .options(joinedload(Event.venue))
            .where(Event.status == EventStatus.PUBLISHED.value)
            .where(Event.event_date > now)
        )

        if category:
            stmt = stmt.where(Event.category == category)

        stmt = stmt.order_by(Event.event_date.asc()).limit(limit)

        query = await self.async_session.execute(statement=stmt)
        return query.scalars().unique().all()

    async def update_event(self, event_id: int, event_update: EventUpdate) -> Event:
        """Update an event"""
        event = await self.read_event_by_id(event_id=event_id)

        update_data = event_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return event

        # Regenerate slug if title changed
        if "title" in update_data:
            update_data["slug"] = await self._generate_unique_slug(
                update_data["title"], exclude_id=event_id
            )

        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(**update_data, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_event_by_id(event_id=event_id)

    async def publish_event(self, event_id: int) -> Event:
        """Publish an event (make it visible to users)"""
        event = await self.read_event_by_id(event_id=event_id)

        if event.status == EventStatus.PUBLISHED.value:
            return event

        if event.status == EventStatus.CANCELLED.value:
            raise ValueError("Cannot publish a cancelled event")

        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                status=EventStatus.PUBLISHED.value,
                published_at=now,
                updated_at=now,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_event_by_id(event_id=event_id)

    async def cancel_event(self, event_id: int) -> Event:
        """Cancel an event"""
        event = await self.read_event_by_id(event_id=event_id)

        if event.status == EventStatus.CANCELLED.value:
            return event

        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                status=EventStatus.CANCELLED.value,
                cancelled_at=now,
                updated_at=now,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_event_by_id(event_id=event_id)

    async def reactivate_event(self, event_id: int) -> Event:
        """Reactivate a cancelled event back to draft status"""
        event = await self.read_event_by_id(event_id=event_id)

        if event.status != EventStatus.CANCELLED.value:
            raise EntityDoesNotExist(f"Event {event_id} is not cancelled and cannot be reactivated")

        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                status=EventStatus.DRAFT.value,
                cancelled_at=None,
                updated_at=now,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_event_by_id(event_id=event_id)

    async def update_seat_counts(
        self,
        event_id: int,
        total_seats: int,
        available_seats: int,
    ) -> None:
        """Update event seat counts"""
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                total_seats=total_seats,
                available_seats=available_seats,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    async def decrement_available_seats(self, event_id: int, count: int = 1) -> None:
        """Decrement available seats count"""
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                available_seats=Event.available_seats - count,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    async def increment_available_seats(self, event_id: int, count: int = 1) -> None:
        """Increment available seats count (for cancellations)"""
        stmt = (
            sqlalchemy.update(Event)
            .where(Event.id == event_id)
            .values(
                available_seats=Event.available_seats + count,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    async def delete_event(self, event_id: int) -> bool:
        """Delete an event (only if draft)"""
        event = await self.read_event_by_id(event_id=event_id)

        if event.status != EventStatus.DRAFT.value:
            raise ValueError("Only draft events can be deleted")

        stmt = sqlalchemy.delete(Event).where(Event.id == event_id)
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    async def get_event_stats(self) -> dict:
        """Get event statistics for admin dashboard"""
        now = datetime.datetime.now(datetime.timezone.utc)

        # Total events
        total_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Event)
        total_result = await self.async_session.execute(statement=total_stmt)
        total_events = total_result.scalar() or 0

        # Published events
        published_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Event).where(
            Event.status == EventStatus.PUBLISHED.value
        )
        published_result = await self.async_session.execute(statement=published_stmt)
        published_events = published_result.scalar() or 0

        # Draft events
        draft_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Event).where(
            Event.status == EventStatus.DRAFT.value
        )
        draft_result = await self.async_session.execute(statement=draft_stmt)
        draft_events = draft_result.scalar() or 0

        # Cancelled events
        cancelled_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Event).where(
            Event.status == EventStatus.CANCELLED.value
        )
        cancelled_result = await self.async_session.execute(statement=cancelled_stmt)
        cancelled_events = cancelled_result.scalar() or 0

        # Completed events (published events where event_date is in the past)
        completed_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Event).where(
            Event.status == EventStatus.PUBLISHED.value,
            Event.event_date < now,
        )
        completed_result = await self.async_session.execute(statement=completed_stmt)
        completed_events = completed_result.scalar() or 0

        return {
            "total": total_events,
            "published": published_events,
            "draft": draft_events,
            "cancelled": cancelled_events,
            "completed": completed_events,
        }
