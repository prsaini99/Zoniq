# Venue CRUD repository -- manages event venue records including creation,
# retrieval with search/filtering, updates, soft deletion (deactivation),
# and permanent deletion.

import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.venue import Venue
from src.models.schemas.venue import VenueCreate, VenueUpdate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class VenueCRUDRepository(BaseCRUDRepository):

    # Creates a new venue record with all provided details including address,
    # capacity, optional seat map configuration, and contact information.
    async def create_venue(self, venue_create: VenueCreate) -> Venue:
        """Create a new venue"""
        new_venue = Venue(
            name=venue_create.name,
            address=venue_create.address,
            city=venue_create.city,
            state=venue_create.state,
            country=venue_create.country,
            pincode=venue_create.pincode,
            capacity=venue_create.capacity,
            seat_map_config=venue_create.seat_map_config,
            contact_phone=venue_create.contact_phone,
            contact_email=venue_create.contact_email,
        )

        self.async_session.add(instance=new_venue)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_venue)

        return new_venue

    # Fetches a venue by its primary key.
    # Raises EntityDoesNotExist if the venue is not found.
    async def read_venue_by_id(self, venue_id: int) -> Venue:
        """Get a venue by ID"""
        stmt = sqlalchemy.select(Venue).where(Venue.id == venue_id)
        query = await self.async_session.execute(statement=stmt)
        venue = query.scalar()

        if not venue:
            raise EntityDoesNotExist(f"Venue with id '{venue_id}' does not exist!")

        return venue

    # Retrieves a paginated list of venues with optional filters: city (partial match),
    # active status, and text search across name, city, and address.
    # Returns both the result set and total count for pagination metadata.
    async def read_venues(
        self,
        page: int = 1,
        page_size: int = 20,
        city: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> tuple[typing.Sequence[Venue], int]:
        """Get venues with pagination and filtering"""
        stmt = sqlalchemy.select(Venue)

        # Apply filters
        if city:
            stmt = stmt.where(Venue.city.ilike(f"%{city}%"))
        if is_active is not None:
            stmt = stmt.where(Venue.is_active == is_active)
        # Search across multiple text fields using case-insensitive ILIKE.
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                sqlalchemy.or_(
                    Venue.name.ilike(search_pattern),
                    Venue.city.ilike(search_pattern),
                    Venue.address.ilike(search_pattern),
                )
            )

        # Count total matching rows before pagination.
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(stmt.subquery())
        count_result = await self.async_session.execute(statement=count_stmt)
        total = count_result.scalar() or 0

        # Order and paginate
        stmt = stmt.order_by(Venue.name.asc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        query = await self.async_session.execute(statement=stmt)
        venues = query.scalars().all()

        return venues, total

    # Returns all active venues sorted alphabetically. Intended for dropdown
    # selectors in the UI where the full list is needed without pagination.
    async def read_all_active_venues(self) -> typing.Sequence[Venue]:
        """Get all active venues (for dropdowns)"""
        stmt = sqlalchemy.select(Venue).where(Venue.is_active == True).order_by(Venue.name.asc())
        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()

    # Partially updates a venue with only the fields provided in the update schema.
    # Returns the refreshed venue after the update.
    async def update_venue(self, venue_id: int, venue_update: VenueUpdate) -> Venue:
        """Update a venue"""
        venue = await self.read_venue_by_id(venue_id=venue_id)

        update_data = venue_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return venue

        stmt = (
            sqlalchemy.update(Venue)
            .where(Venue.id == venue_id)
            .values(**update_data, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_venue_by_id(venue_id=venue_id)

    # Soft-deletes a venue by setting is_active=False. The record is preserved
    # for historical reference (existing events may still reference it).
    async def delete_venue(self, venue_id: int) -> bool:
        """Delete a venue (soft delete by setting is_active=False)"""
        venue = await self.read_venue_by_id(venue_id=venue_id)

        stmt = (
            sqlalchemy.update(Venue)
            .where(Venue.id == venue_id)
            .values(is_active=False, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    # Permanently removes a venue from the database. Use with caution --
    # will fail if foreign key constraints reference this venue.
    async def hard_delete_venue(self, venue_id: int) -> bool:
        """Permanently delete a venue"""
        venue = await self.read_venue_by_id(venue_id=venue_id)

        stmt = sqlalchemy.delete(Venue).where(Venue.id == venue_id)
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True
