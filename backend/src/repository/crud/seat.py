import datetime
import typing

import sqlalchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.seat import Seat, SeatStatus
from src.models.schemas.event import SeatCreate, SeatBulkCreate, SeatUpdate
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class SeatCRUDRepository(BaseCRUDRepository):

    async def create_seat(
        self,
        event_id: int,
        seat_create: SeatCreate,
    ) -> Seat:
        """Create a single seat"""
        new_seat = Seat(
            event_id=event_id,
            category_id=seat_create.category_id,
            seat_number=seat_create.seat_number,
            row_name=seat_create.row_name,
            section=seat_create.section,
            position_x=seat_create.position_x,
            position_y=seat_create.position_y,
            status=SeatStatus.AVAILABLE.value,
        )

        self.async_session.add(instance=new_seat)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_seat)

        return new_seat

    async def bulk_create_seats(
        self,
        event_id: int,
        bulk_create: SeatBulkCreate,
    ) -> list[Seat]:
        """Bulk create seats for an event"""
        seats = []
        for row in bulk_create.rows:
            for seat_num in range(1, bulk_create.seats_per_row + 1):
                seat = Seat(
                    event_id=event_id,
                    category_id=bulk_create.category_id,
                    seat_number=str(seat_num),
                    row_name=row,
                    section=bulk_create.section,
                    status=SeatStatus.AVAILABLE.value,
                )
                seats.append(seat)
                self.async_session.add(instance=seat)

        await self.async_session.commit()

        # Refresh all seats to get their IDs
        for seat in seats:
            await self.async_session.refresh(instance=seat)

        return seats

    async def read_seat_by_id(self, seat_id: int) -> Seat:
        """Get a seat by ID"""
        stmt = (
            sqlalchemy.select(Seat)
            .options(joinedload(Seat.category))
            .where(Seat.id == seat_id)
        )
        query = await self.async_session.execute(statement=stmt)
        seat = query.scalar()

        if not seat:
            raise EntityDoesNotExist(f"Seat with id '{seat_id}' does not exist!")

        return seat

    async def read_seats_by_event(
        self,
        event_id: int,
        category_id: int | None = None,
        status: str | None = None,
        include_category: bool = False,
    ) -> typing.Sequence[Seat]:
        """Get all seats for an event"""
        stmt = sqlalchemy.select(Seat).where(Seat.event_id == event_id)

        if include_category:
            stmt = stmt.options(joinedload(Seat.category))

        if category_id:
            stmt = stmt.where(Seat.category_id == category_id)

        if status:
            stmt = stmt.where(Seat.status == status)

        stmt = stmt.order_by(Seat.section, Seat.row_name, Seat.seat_number)

        query = await self.async_session.execute(statement=stmt)
        return query.scalars().unique().all()

    async def read_available_seats_by_event(
        self,
        event_id: int,
        category_id: int | None = None,
    ) -> typing.Sequence[Seat]:
        """Get available seats for an event"""
        now = datetime.datetime.now(datetime.timezone.utc)

        stmt = sqlalchemy.select(Seat).where(
            Seat.event_id == event_id,
            sqlalchemy.or_(
                Seat.status == SeatStatus.AVAILABLE.value,
                sqlalchemy.and_(
                    Seat.status == SeatStatus.LOCKED.value,
                    Seat.locked_until < now,  # Lock expired
                ),
            ),
        )

        if category_id:
            stmt = stmt.where(Seat.category_id == category_id)

        stmt = stmt.order_by(Seat.section, Seat.row_name, Seat.seat_number)

        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()

    async def update_seat(
        self,
        seat_id: int,
        seat_update: SeatUpdate,
    ) -> Seat:
        """Update a seat"""
        seat = await self.read_seat_by_id(seat_id=seat_id)

        update_data = seat_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return seat

        stmt = (
            sqlalchemy.update(Seat)
            .where(Seat.id == seat_id)
            .values(**update_data, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_seat_by_id(seat_id=seat_id)

    async def lock_seats(
        self,
        seat_ids: list[int],
        user_id: int,
        lock_duration_minutes: int = 7,
    ) -> list[Seat]:
        """Lock seats for a user during checkout"""
        now = datetime.datetime.now(datetime.timezone.utc)
        lock_until = now + datetime.timedelta(minutes=lock_duration_minutes)

        # Update seats that are available or have expired locks
        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.id.in_(seat_ids),
                sqlalchemy.or_(
                    Seat.status == SeatStatus.AVAILABLE.value,
                    sqlalchemy.and_(
                        Seat.status == SeatStatus.LOCKED.value,
                        Seat.locked_until < now,
                    ),
                ),
            )
            .values(
                status=SeatStatus.LOCKED.value,
                locked_by=user_id,
                locked_until=lock_until,
                updated_at=now,
            )
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        # Return the locked seats
        locked_seats = []
        for seat_id in seat_ids:
            try:
                seat = await self.read_seat_by_id(seat_id=seat_id)
                if seat.status == SeatStatus.LOCKED.value and seat.locked_by == user_id:
                    locked_seats.append(seat)
            except EntityDoesNotExist:
                pass

        return locked_seats

    async def unlock_seats(
        self,
        seat_ids: list[int],
        user_id: int | None = None,
    ) -> int:
        """Unlock seats (release lock)"""
        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.id.in_(seat_ids),
                Seat.status == SeatStatus.LOCKED.value,
            )
            .values(
                status=SeatStatus.AVAILABLE.value,
                locked_by=None,
                locked_until=None,
                updated_at=sqlalchemy_functions.now(),
            )
        )

        if user_id:
            stmt = stmt.where(Seat.locked_by == user_id)

        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount

    async def release_expired_locks(self) -> int:
        """Release all expired seat locks"""
        now = datetime.datetime.now(datetime.timezone.utc)

        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.status == SeatStatus.LOCKED.value,
                Seat.locked_until < now,
            )
            .values(
                status=SeatStatus.AVAILABLE.value,
                locked_by=None,
                locked_until=None,
                updated_at=now,
            )
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount

    async def book_seats(
        self,
        seat_ids: list[int],
        booking_id: int,
    ) -> int:
        """Mark seats as booked"""
        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.id.in_(seat_ids),
                Seat.status.in_([SeatStatus.LOCKED.value, SeatStatus.AVAILABLE.value]),
            )
            .values(
                status=SeatStatus.BOOKED.value,
                booking_id=booking_id,
                locked_by=None,
                locked_until=None,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount

    async def unbook_seats(
        self,
        seat_ids: list[int],
    ) -> int:
        """Unbook seats (for cancellations)"""
        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.id.in_(seat_ids),
                Seat.status == SeatStatus.BOOKED.value,
            )
            .values(
                status=SeatStatus.AVAILABLE.value,
                booking_id=None,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount

    async def block_seat(self, seat_id: int) -> Seat:
        """Block a seat (admin only - not for sale)"""
        stmt = (
            sqlalchemy.update(Seat)
            .where(Seat.id == seat_id)
            .values(
                status=SeatStatus.BLOCKED.value,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_seat_by_id(seat_id=seat_id)

    async def unblock_seat(self, seat_id: int) -> Seat:
        """Unblock a seat"""
        stmt = (
            sqlalchemy.update(Seat)
            .where(
                Seat.id == seat_id,
                Seat.status == SeatStatus.BLOCKED.value,
            )
            .values(
                status=SeatStatus.AVAILABLE.value,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_seat_by_id(seat_id=seat_id)

    async def delete_seat(self, seat_id: int) -> bool:
        """Delete a seat (only if available)"""
        seat = await self.read_seat_by_id(seat_id=seat_id)

        if seat.status not in [SeatStatus.AVAILABLE.value, SeatStatus.BLOCKED.value]:
            raise ValueError("Cannot delete a locked or booked seat")

        stmt = sqlalchemy.delete(Seat).where(Seat.id == seat_id)
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return True

    async def delete_seats_by_event(self, event_id: int) -> int:
        """Delete all seats for an event"""
        stmt = sqlalchemy.delete(Seat).where(Seat.event_id == event_id)
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return result.rowcount

    async def get_seat_counts_by_event(self, event_id: int) -> dict:
        """Get seat counts by status for an event"""
        stmt = (
            sqlalchemy.select(
                Seat.status,
                sqlalchemy.func.count(Seat.id).label("count"),
            )
            .where(Seat.event_id == event_id)
            .group_by(Seat.status)
        )
        result = await self.async_session.execute(statement=stmt)
        rows = result.all()

        counts = {status.value: 0 for status in SeatStatus}
        for row in rows:
            counts[row.status] = row.count

        return counts
