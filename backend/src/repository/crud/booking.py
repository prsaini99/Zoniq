import datetime
import typing

import sqlalchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.booking import Booking, BookingItem
from src.models.db.cart import Cart
from src.models.db.seat import Seat, SeatStatus
from src.models.db.seat_category import SeatCategory
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class BookingCRUDRepository(BaseCRUDRepository):

    async def create_booking_from_cart(
        self,
        cart: Cart,
        user_id: int,
        contact_email: str | None = None,
        contact_phone: str | None = None,
    ) -> Booking:
        """Create a booking from a cart, generating booking items and marking seats as booked."""
        # Calculate totals
        subtotal = sum(float(item.unit_price) * item.quantity for item in cart.items)
        final_amount = subtotal
        ticket_count = sum(item.quantity for item in cart.items)

        # Create booking with pending status (awaiting Razorpay payment)
        booking = Booking(
            booking_number=Booking.generate_booking_number(),
            user_id=user_id,
            event_id=cart.event_id,
            status="pending",
            total_amount=subtotal,
            discount_amount=0.0,
            final_amount=final_amount,
            payment_status="pending",  # Requires Razorpay payment to complete
            ticket_count=ticket_count,
            contact_email=contact_email,
            contact_phone=contact_phone,
        )
        self.async_session.add(booking)
        await self.async_session.flush()  # Get booking.id

        # Create booking items from cart items
        for cart_item in cart.items:
            seat_ids = cart_item.seat_ids or []
            if seat_ids:
                # Assigned seating: create one BookingItem per seat
                for seat_id in seat_ids:
                    # Get seat label
                    seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                    seat_result = await self.async_session.execute(seat_stmt)
                    seat = seat_result.scalar_one_or_none()

                    booking_item = BookingItem(
                        booking_id=booking.id,
                        seat_id=seat_id,
                        category_id=cart_item.seat_category_id,
                        price=cart_item.unit_price,
                        category_name=cart_item.seat_category.name if cart_item.seat_category else "Unknown",
                        seat_label=seat.seat_label if seat else None,
                        ticket_number=BookingItem.generate_ticket_number(),
                    )
                    self.async_session.add(booking_item)

                    # Mark seat as booked
                    if seat:
                        seat.status = SeatStatus.BOOKED.value
                        seat.booking_id = booking.id
                        seat.locked_until = None
                        seat.locked_by = None
            else:
                # General admission: create quantity BookingItems
                for _ in range(cart_item.quantity):
                    booking_item = BookingItem(
                        booking_id=booking.id,
                        seat_id=None,
                        category_id=cart_item.seat_category_id,
                        price=cart_item.unit_price,
                        category_name=cart_item.seat_category.name if cart_item.seat_category else "Unknown",
                        seat_label=None,
                        ticket_number=BookingItem.generate_ticket_number(),
                    )
                    self.async_session.add(booking_item)

                # Decrement available seats for the category
                cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == cart_item.seat_category_id)
                cat_result = await self.async_session.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                if category:
                    category.available_seats = max(0, category.available_seats - cart_item.quantity)

        # Update event available seats
        from src.models.db.event import Event
        event_stmt = sqlalchemy.select(Event).where(Event.id == cart.event_id)
        event_result = await self.async_session.execute(event_stmt)
        event = event_result.scalar_one_or_none()
        if event:
            event.available_seats = max(0, event.available_seats - ticket_count)

        # Mark cart as converted
        cart.status = "converted"
        cart.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()

        # Reload booking with relationships
        return await self.read_booking_by_id(booking.id)

    async def read_booking_by_id(self, booking_id: int) -> Booking:
        """Get a booking by ID with all relationships"""
        stmt = (
            sqlalchemy.select(Booking)
            .options(
                joinedload(Booking.items).joinedload(BookingItem.category),
                joinedload(Booking.event),
            )
            .where(Booking.id == booking_id)
        )
        result = await self.async_session.execute(stmt)
        booking = result.unique().scalar_one_or_none()
        if not booking:
            raise EntityDoesNotExist(f"Booking with id {booking_id} does not exist!")
        return booking

    async def read_booking_by_number(self, booking_number: str) -> Booking:
        """Get a booking by booking number"""
        stmt = (
            sqlalchemy.select(Booking)
            .options(
                joinedload(Booking.items).joinedload(BookingItem.category),
                joinedload(Booking.event),
            )
            .where(Booking.booking_number == booking_number)
        )
        result = await self.async_session.execute(stmt)
        booking = result.unique().scalar_one_or_none()
        if not booking:
            raise EntityDoesNotExist(f"Booking with number {booking_number} does not exist!")
        return booking

    async def read_bookings_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: str | None = None,
    ) -> tuple[list[Booking], int]:
        """Get paginated bookings for a user"""
        # Count query
        count_stmt = (
            sqlalchemy.select(sqlalchemy_functions.count())
            .select_from(Booking)
            .where(Booking.user_id == user_id)
        )
        if status:
            count_stmt = count_stmt.where(Booking.status == status)
        count_result = await self.async_session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Data query
        stmt = (
            sqlalchemy.select(Booking)
            .options(joinedload(Booking.event))
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        if status:
            stmt = stmt.where(Booking.status == status)
        result = await self.async_session.execute(stmt)
        bookings = list(result.unique().scalars().all())

        return bookings, total

    async def release_seats_for_failed_payment(self, booking_id: int) -> Booking:
        """Release seats when payment fails - revert the booking to allow retry or release seats."""
        booking = await self.read_booking_by_id(booking_id)

        # Only process pending bookings with pending/failed payment
        if booking.status != "pending" or booking.payment_status not in ("pending", "failed"):
            return booking

        # Release seats
        for item in booking.items:
            if item.seat_id:
                seat_stmt = sqlalchemy.select(Seat).where(Seat.id == item.seat_id)
                seat_result = await self.async_session.execute(seat_stmt)
                seat = seat_result.scalar_one_or_none()
                if seat:
                    seat.status = SeatStatus.AVAILABLE.value
                    seat.booking_id = None

        # Restore available seats on category + event
        from src.models.db.event import Event
        category_quantities: dict[int, int] = {}
        for item in booking.items:
            category_quantities[item.category_id] = category_quantities.get(item.category_id, 0) + 1

        for cat_id, qty in category_quantities.items():
            cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == cat_id)
            cat_result = await self.async_session.execute(cat_stmt)
            category = cat_result.scalar_one_or_none()
            if category:
                category.available_seats += qty

        event_stmt = sqlalchemy.select(Event).where(Event.id == booking.event_id)
        event_result = await self.async_session.execute(event_stmt)
        event = event_result.scalar_one_or_none()
        if event:
            event.available_seats += booking.ticket_count

        # Update booking status to failed
        now = datetime.datetime.now(datetime.timezone.utc)
        booking.status = "failed"
        booking.payment_status = "failed"
        booking.updated_at = now

        await self.async_session.commit()
        return booking

    async def cancel_booking(self, booking_id: int, user_id: int) -> Booking:
        """Cancel a booking and release seats"""
        booking = await self.read_booking_by_id(booking_id)

        if booking.user_id != user_id:
            raise ValueError("You can only cancel your own bookings")

        if booking.status not in ("pending", "confirmed"):
            raise ValueError(f"Cannot cancel a booking with status '{booking.status}'")

        # Release seats
        for item in booking.items:
            if item.seat_id:
                seat_stmt = sqlalchemy.select(Seat).where(Seat.id == item.seat_id)
                seat_result = await self.async_session.execute(seat_stmt)
                seat = seat_result.scalar_one_or_none()
                if seat:
                    seat.status = SeatStatus.AVAILABLE.value
                    seat.booking_id = None

        # Restore available seats on category + event
        from src.models.db.event import Event
        category_quantities: dict[int, int] = {}
        for item in booking.items:
            category_quantities[item.category_id] = category_quantities.get(item.category_id, 0) + 1

        for cat_id, qty in category_quantities.items():
            cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == cat_id)
            cat_result = await self.async_session.execute(cat_stmt)
            category = cat_result.scalar_one_or_none()
            if category:
                category.available_seats += qty

        event_stmt = sqlalchemy.select(Event).where(Event.id == booking.event_id)
        event_result = await self.async_session.execute(event_stmt)
        event = event_result.scalar_one_or_none()
        if event:
            event.available_seats += booking.ticket_count

        # Update booking status
        now = datetime.datetime.now(datetime.timezone.utc)
        booking.status = "cancelled"
        booking.payment_status = "refunded"
        booking.cancelled_at = now
        booking.updated_at = now

        await self.async_session.commit()
        return booking
