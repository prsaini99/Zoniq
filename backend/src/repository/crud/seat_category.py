# Seat Category CRUD repository -- manages seat categories (pricing tiers) for events.
# Each event can have multiple categories (e.g., VIP, Standard, Economy) with
# independent pricing, seat counts, and display configuration.

import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.seat_category import SeatCategory
from src.models.schemas.event import SeatCategoryCreate, SeatCategoryUpdate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist, EntityAlreadyExists


class SeatCategoryCRUDRepository(BaseCRUDRepository):

    # Creates a new seat category for an event. Validates that the category name is
    # unique within the event. Initially sets available_seats equal to total_seats.
    async def create_category(
        self,
        event_id: int,
        category_create: SeatCategoryCreate,
    ) -> SeatCategory:
        """Create a new seat category for an event"""
        # Check if category name already exists for this event
        existing = await self._get_category_by_name(event_id, category_create.name)
        if existing:
            raise EntityAlreadyExists(
                f"Category '{category_create.name}' already exists for this event"
            )

        new_category = SeatCategory(
            event_id=event_id,
            name=category_create.name,
            description=category_create.description,
            price=category_create.price,
            total_seats=category_create.total_seats,
            available_seats=category_create.total_seats,  # Initially all seats available
            display_order=category_create.display_order,
            color_code=category_create.color_code,
        )

        self.async_session.add(instance=new_category)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_category)

        return new_category

    # Looks up a seat category by name within a specific event.
    # Used internally to enforce name uniqueness per event.
    async def _get_category_by_name(
        self,
        event_id: int,
        name: str,
    ) -> SeatCategory | None:
        """Get category by name for an event"""
        stmt = sqlalchemy.select(SeatCategory).where(
            SeatCategory.event_id == event_id,
            SeatCategory.name == name,
        )
        query = await self.async_session.execute(statement=stmt)
        return query.scalar()

    # Fetches a seat category by its primary key.
    # Raises EntityDoesNotExist if no matching category is found.
    async def read_category_by_id(self, category_id: int) -> SeatCategory:
        """Get a category by ID"""
        stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == category_id)
        query = await self.async_session.execute(statement=stmt)
        category = query.scalar()

        if not category:
            raise EntityDoesNotExist(f"Seat category with id '{category_id}' does not exist!")

        return category

    # Retrieves all seat categories for an event, optionally filtering to active-only.
    # Ordered by display_order first, then alphabetically by name.
    async def read_categories_by_event(
        self,
        event_id: int,
        active_only: bool = False,
    ) -> typing.Sequence[SeatCategory]:
        """Get all seat categories for an event"""
        stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.event_id == event_id)

        if active_only:
            stmt = stmt.where(SeatCategory.is_active == True)

        stmt = stmt.order_by(SeatCategory.display_order.asc(), SeatCategory.name.asc())

        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()

    # Updates a seat category with the provided fields. If total_seats is changed,
    # available_seats is recalculated: new_available = new_total - already_sold.
    # Prevents reducing total below the number of already-sold seats.
    async def update_category(
        self,
        category_id: int,
        category_update: SeatCategoryUpdate,
    ) -> SeatCategory:
        """Update a seat category"""
        category = await self.read_category_by_id(category_id=category_id)

        update_data = category_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return category

        # If total_seats is being updated, adjust available_seats proportionally
        # Ensure the new total is not less than the number of seats already sold.
        if "total_seats" in update_data:
            sold_seats = category.total_seats - category.available_seats
            new_total = update_data["total_seats"]
            if new_total < sold_seats:
                raise ValueError(
                    f"Cannot reduce total seats below {sold_seats} (already sold)"
                )
            # Recalculate available seats: new_total minus already sold.
            update_data["available_seats"] = new_total - sold_seats

        stmt = (
            sqlalchemy.update(SeatCategory)
            .where(SeatCategory.id == category_id)
            .values(**update_data, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_category_by_id(category_id=category_id)

    # Permanently deletes a seat category. Only allowed if no seats have been sold
    # (i.e., available_seats equals total_seats) to prevent orphaned booking items.
    async def delete_category(self, category_id: int) -> bool:
        """Delete a seat category (only if no seats sold)"""
        category = await self.read_category_by_id(category_id=category_id)

        # If available < total, some seats have been sold and deletion is not safe.
        if category.available_seats < category.total_seats:
            raise ValueError("Cannot delete category with sold seats")

        stmt = sqlalchemy.delete(SeatCategory).where(SeatCategory.id == category_id)
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    # Atomically decrements the available seat count using a SQL expression.
    # Used during booking to reduce availability without loading the full object.
    async def decrement_available_seats(
        self,
        category_id: int,
        count: int = 1,
    ) -> None:
        """Decrement available seats count"""
        stmt = (
            sqlalchemy.update(SeatCategory)
            .where(SeatCategory.id == category_id)
            .values(
                available_seats=SeatCategory.available_seats - count,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Atomically increments the available seat count using a SQL expression.
    # Used when bookings are cancelled or payments fail to restore availability.
    async def increment_available_seats(
        self,
        category_id: int,
        count: int = 1,
    ) -> None:
        """Increment available seats count (for cancellations)"""
        stmt = (
            sqlalchemy.update(SeatCategory)
            .where(SeatCategory.id == category_id)
            .values(
                available_seats=SeatCategory.available_seats + count,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Aggregates total and available seats across all active categories for an event.
    # Returns a tuple of (total_seats, available_seats). Used to update event-level counts.
    async def get_total_seats_for_event(self, event_id: int) -> tuple[int, int]:
        """Get total and available seats for an event across all categories"""
        stmt = sqlalchemy.select(
            sqlalchemy.func.sum(SeatCategory.total_seats),
            sqlalchemy.func.sum(SeatCategory.available_seats),
        ).where(
            SeatCategory.event_id == event_id,
            SeatCategory.is_active == True,
        )
        result = await self.async_session.execute(statement=stmt)
        row = result.one()
        return (row[0] or 0, row[1] or 0)
