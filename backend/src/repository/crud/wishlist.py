# Wishlist CRUD repository -- manages user wishlists for events.
# Allows users to save published events for later, retrieve their full wishlist,
# remove events, and check wishlist membership.

"""
Wishlist CRUD Repository
"""
import typing

import sqlalchemy
from sqlalchemy.orm import joinedload

from src.models.db.wishlist import Wishlist
from src.models.db.event import Event, EventStatus
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists


class WishlistCRUDRepository(BaseCRUDRepository):

    # Retrieves all wishlist items for a user with eager-loaded event and venue data.
    # Ordered by most recently added first.
    async def get_user_wishlist(
        self,
        account_id: int,
    ) -> typing.Sequence[Wishlist]:
        """Get all wishlist items for a user with event details"""
        stmt = (
            sqlalchemy.select(Wishlist)
            .options(joinedload(Wishlist.event).joinedload(Event.venue))
            .where(Wishlist.account_id == account_id)
            .order_by(Wishlist.created_at.desc())
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalars().unique().all()

    # Adds an event to the user's wishlist. Validates that the event exists and
    # is published (only published events can be wishlisted). Prevents duplicates
    # by checking for an existing wishlist entry first. Returns the created item
    # with eager-loaded event and venue relationships.
    async def add_to_wishlist(
        self,
        account_id: int,
        event_id: int,
    ) -> Wishlist:
        """Add an event to user's wishlist"""
        # Check if already in wishlist
        existing = await self.get_wishlist_item(account_id, event_id)
        if existing:
            raise EntityAlreadyExists("Event is already in your wishlist")

        # Verify event exists and is published
        # Only published events are available for wishlisting.
        event_stmt = sqlalchemy.select(Event).where(
            Event.id == event_id,
            Event.status == EventStatus.PUBLISHED.value,
        )
        event_result = await self.async_session.execute(statement=event_stmt)
        event = event_result.scalar()
        if not event:
            raise EntityDoesNotExist("Event not found or not available")

        # Create wishlist item
        wishlist_item = Wishlist(
            account_id=account_id,
            event_id=event_id,
        )
        self.async_session.add(instance=wishlist_item)
        await self.async_session.commit()
        await self.async_session.refresh(instance=wishlist_item)

        # Load the event relationship for the response.
        stmt = (
            sqlalchemy.select(Wishlist)
            .options(joinedload(Wishlist.event).joinedload(Event.venue))
            .where(Wishlist.id == wishlist_item.id)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar_one()

    # Removes an event from the user's wishlist by deleting the matching record.
    # Raises EntityDoesNotExist if the event was not in the wishlist (rowcount == 0).
    async def remove_from_wishlist(
        self,
        account_id: int,
        event_id: int,
    ) -> None:
        """Remove an event from user's wishlist"""
        stmt = sqlalchemy.delete(Wishlist).where(
            Wishlist.account_id == account_id,
            Wishlist.event_id == event_id,
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        if result.rowcount == 0:
            raise EntityDoesNotExist("Event not found in your wishlist")

    # Fetches a single wishlist entry for a user+event combination.
    # Returns None if the event is not in the user's wishlist.
    async def get_wishlist_item(
        self,
        account_id: int,
        event_id: int,
    ) -> Wishlist | None:
        """Check if an event is in user's wishlist"""
        stmt = sqlalchemy.select(Wishlist).where(
            Wishlist.account_id == account_id,
            Wishlist.event_id == event_id,
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar()

    # Boolean convenience method to check if an event is in a user's wishlist.
    # Delegates to get_wishlist_item and converts the result to a boolean.
    async def is_in_wishlist(
        self,
        account_id: int,
        event_id: int,
    ) -> bool:
        """Check if an event is in user's wishlist"""
        item = await self.get_wishlist_item(account_id, event_id)
        return item is not None
