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

        # Load the event relationship
        stmt = (
            sqlalchemy.select(Wishlist)
            .options(joinedload(Wishlist.event).joinedload(Event.venue))
            .where(Wishlist.id == wishlist_item.id)
        )
        result = await self.async_session.execute(statement=stmt)
        return result.scalar_one()

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

    async def is_in_wishlist(
        self,
        account_id: int,
        event_id: int,
    ) -> bool:
        """Check if an event is in user's wishlist"""
        item = await self.get_wishlist_item(account_id, event_id)
        return item is not None
