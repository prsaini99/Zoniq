import datetime
import typing

import sqlalchemy
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.cart import Cart, CartItem
from src.models.db.seat import Seat, SeatStatus
from src.models.db.seat_category import SeatCategory
from src.models.schemas.cart import CartAddItem, CartUpdateItem
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist

# Cart session duration in minutes
CART_EXPIRY_MINUTES = 15
SEAT_LOCK_MINUTES = 7


class CartCRUDRepository(BaseCRUDRepository):

    async def get_or_create_cart(
        self,
        user_id: int,
        event_id: int,
    ) -> Cart:
        """Get active cart for user+event, or create a new one."""
        # First expire any old carts for this user+event
        await self._expire_old_carts(user_id, event_id)

        # Look for existing active cart
        stmt = (
            sqlalchemy.select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.seat_category),
                joinedload(Cart.event),
            )
            .where(
                Cart.user_id == user_id,
                Cart.event_id == event_id,
                Cart.status == "active",
            )
        )
        result = await self.async_session.execute(stmt)
        cart = result.unique().scalar_one_or_none()

        if cart and not cart.is_expired:
            return cart

        # If expired, mark it
        if cart and cart.is_expired:
            cart.status = "expired"
            await self._release_cart_seats(cart)

        # Create new cart
        now = datetime.datetime.now(datetime.timezone.utc)
        new_cart = Cart(
            user_id=user_id,
            event_id=event_id,
            status="active",
            expires_at=now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES),
        )
        self.async_session.add(new_cart)
        await self.async_session.flush()

        # Reload with relationships
        return await self._load_cart(new_cart.id)

    async def add_item(
        self,
        cart_id: int,
        item_data: CartAddItem,
        user_id: int,
    ) -> Cart:
        """Add an item to the cart, locking seats if applicable."""
        cart = await self._load_cart(cart_id)

        if not cart or cart.status != "active":
            raise ValueError("Cart is not active")
        if cart.is_expired:
            cart.status = "expired"
            await self._release_cart_seats(cart)
            await self.async_session.commit()
            raise ValueError("Cart has expired. Please start a new cart.")

        # Get seat category and verify it belongs to the event
        cat_stmt = sqlalchemy.select(SeatCategory).where(
            SeatCategory.id == item_data.seat_category_id,
            SeatCategory.event_id == cart.event_id,
            SeatCategory.is_active == True,
        )
        cat_result = await self.async_session.execute(cat_stmt)
        category = cat_result.scalar_one_or_none()
        if not category:
            raise ValueError("Invalid seat category for this event")

        # Check if user already has this category in cart
        existing = next(
            (i for i in cart.items if i.seat_category_id == item_data.seat_category_id),
            None,
        )
        if existing:
            raise ValueError("This category is already in your cart. Update quantity instead.")

        # Check availability
        if category.available_seats < item_data.quantity:
            raise ValueError(f"Only {category.available_seats} seats available in {category.name}")

        # Lock specific seats if assigned seating
        now = datetime.datetime.now(datetime.timezone.utc)
        lock_until = now + datetime.timedelta(minutes=SEAT_LOCK_MINUTES)
        seat_ids = None

        if item_data.seat_ids:
            # Verify seats are available and lock them
            for seat_id in item_data.seat_ids:
                seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                seat_result = await self.async_session.execute(seat_stmt)
                seat = seat_result.scalar_one_or_none()
                if not seat or not seat.is_available:
                    raise ValueError(f"Seat {seat_id} is not available")
                if seat.category_id != item_data.seat_category_id:
                    raise ValueError(f"Seat {seat_id} does not belong to the selected category")

                # Lock the seat
                seat.status = SeatStatus.LOCKED.value
                seat.locked_until = lock_until
                seat.locked_by = user_id

            seat_ids = item_data.seat_ids

        # Create cart item
        cart_item = CartItem(
            cart_id=cart_id,
            seat_category_id=item_data.seat_category_id,
            seat_ids=seat_ids,
            quantity=len(item_data.seat_ids) if item_data.seat_ids else item_data.quantity,
            unit_price=category.price,
            locked_until=lock_until if seat_ids else None,
        )
        self.async_session.add(cart_item)

        # Extend cart expiry
        cart.expires_at = now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES)
        cart.updated_at = now

        await self.async_session.commit()
        return await self._load_cart(cart_id)

    async def update_item(
        self,
        cart_id: int,
        item_id: int,
        update_data: CartUpdateItem,
        user_id: int,
    ) -> Cart:
        """Update cart item quantity (general admission only)."""
        cart = await self._load_cart(cart_id)
        if not cart or cart.status != "active":
            raise ValueError("Cart is not active")

        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise EntityDoesNotExist(f"Cart item {item_id} not found")

        if item.seat_ids:
            raise ValueError("Cannot change quantity for assigned seats. Remove and re-add instead.")

        # Check availability
        cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == item.seat_category_id)
        cat_result = await self.async_session.execute(cat_stmt)
        category = cat_result.scalar_one_or_none()
        if category and category.available_seats < update_data.quantity:
            raise ValueError(f"Only {category.available_seats} seats available")

        item.quantity = update_data.quantity
        now = datetime.datetime.now(datetime.timezone.utc)
        cart.updated_at = now
        cart.expires_at = now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES)

        await self.async_session.commit()
        return await self._load_cart(cart_id)

    async def remove_item(
        self,
        cart_id: int,
        item_id: int,
        user_id: int,
    ) -> Cart:
        """Remove an item from the cart and release locked seats."""
        cart = await self._load_cart(cart_id)
        if not cart:
            raise EntityDoesNotExist(f"Cart {cart_id} not found")

        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise EntityDoesNotExist(f"Cart item {item_id} not found")

        # Release locked seats
        if item.seat_ids:
            for seat_id in item.seat_ids:
                seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                seat_result = await self.async_session.execute(seat_stmt)
                seat = seat_result.scalar_one_or_none()
                if seat and seat.locked_by == user_id:
                    seat.status = SeatStatus.AVAILABLE.value
                    seat.locked_until = None
                    seat.locked_by = None

        await self.async_session.delete(item)
        cart.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
        return await self._load_cart(cart_id)

    async def validate_cart(self, cart_id: int) -> tuple[bool, list[str], list[str]]:
        """Validate cart before checkout. Returns (is_valid, errors, warnings)."""
        cart = await self._load_cart(cart_id)
        errors: list[str] = []
        warnings: list[str] = []

        if not cart:
            return False, ["Cart not found"], []
        if cart.status != "active":
            return False, ["Cart is not active"], []
        if cart.is_expired:
            return False, ["Cart has expired"], []
        if not cart.items:
            return False, ["Cart is empty"], []

        # Check event is still bookable
        from src.models.db.event import Event
        event_stmt = sqlalchemy.select(Event).where(Event.id == cart.event_id)
        event_result = await self.async_session.execute(event_stmt)
        event = event_result.scalar_one_or_none()

        if not event:
            errors.append("Event no longer exists")
        elif not event.is_booking_open:
            errors.append("Booking is no longer open for this event")

        # Check each item's seats are still locked/available
        for item in cart.items:
            if item.seat_ids:
                for seat_id in item.seat_ids:
                    seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                    seat_result = await self.async_session.execute(seat_stmt)
                    seat = seat_result.scalar_one_or_none()
                    if not seat:
                        errors.append(f"Seat no longer available")
                    elif seat.status == SeatStatus.LOCKED.value and seat.is_locked:
                        continue  # Still locked by user
                    elif seat.status == SeatStatus.AVAILABLE.value:
                        warnings.append(f"Seat lock expired, re-locking required")
                    else:
                        errors.append(f"Seat has been taken by another user")
            else:
                # Check category availability
                cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == item.seat_category_id)
                cat_result = await self.async_session.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                if category and category.available_seats < item.quantity:
                    errors.append(f"Only {category.available_seats} seats available in {category.name}")

        return len(errors) == 0, errors, warnings

    async def get_user_active_cart(self, user_id: int, event_id: int | None = None) -> Cart | None:
        """Get user's active cart, optionally for a specific event."""
        stmt = (
            sqlalchemy.select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.seat_category),
                joinedload(Cart.event),
            )
            .where(Cart.user_id == user_id, Cart.status == "active")
        )
        if event_id:
            stmt = stmt.where(Cart.event_id == event_id)
        stmt = stmt.order_by(Cart.updated_at.desc())

        result = await self.async_session.execute(stmt)
        cart = result.unique().scalar_one_or_none()

        if cart and cart.is_expired:
            cart.status = "expired"
            await self._release_cart_seats(cart)
            await self.async_session.commit()
            return None

        return cart

    async def get_cart_count(self, user_id: int) -> int:
        """Get total item count across all active carts for a user."""
        stmt = (
            sqlalchemy.select(sqlalchemy_functions.coalesce(sqlalchemy_functions.sum(CartItem.quantity), 0))
            .join(Cart, Cart.id == CartItem.cart_id)
            .where(
                Cart.user_id == user_id,
                Cart.status == "active",
                Cart.expires_at > datetime.datetime.now(datetime.timezone.utc),
            )
        )
        result = await self.async_session.execute(stmt)
        return int(result.scalar() or 0)

    # ===== Private helpers =====

    async def _load_cart(self, cart_id: int) -> Cart | None:
        """Load cart with all relationships."""
        stmt = (
            sqlalchemy.select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.seat_category),
                joinedload(Cart.event),
            )
            .where(Cart.id == cart_id)
        )
        result = await self.async_session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def _expire_old_carts(self, user_id: int, event_id: int) -> None:
        """Expire old active carts for this user+event."""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = (
            sqlalchemy.select(Cart)
            .options(joinedload(Cart.items))
            .where(
                Cart.user_id == user_id,
                Cart.event_id == event_id,
                Cart.status == "active",
                Cart.expires_at < now,
            )
        )
        result = await self.async_session.execute(stmt)
        expired_carts = result.unique().scalars().all()

        for cart in expired_carts:
            cart.status = "expired"
            await self._release_cart_seats(cart)

        if expired_carts:
            await self.async_session.flush()

    async def _release_cart_seats(self, cart: Cart) -> None:
        """Release all locked seats in a cart."""
        for item in cart.items:
            if item.seat_ids:
                for seat_id in item.seat_ids:
                    seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                    seat_result = await self.async_session.execute(seat_stmt)
                    seat = seat_result.scalar_one_or_none()
                    if seat and seat.status == SeatStatus.LOCKED.value:
                        seat.status = SeatStatus.AVAILABLE.value
                        seat.locked_until = None
                        seat.locked_by = None

    async def abandon_cart(self, cart_id: int, user_id: int) -> None:
        """Abandon/clear a cart and release all locked seats."""
        cart = await self._load_cart(cart_id)
        if not cart:
            return

        if cart.user_id != user_id:
            raise ValueError("Cannot abandon another user's cart")

        # Release any locked seats
        await self._release_cart_seats(cart)

        # Mark cart as abandoned
        cart.status = "abandoned"
        cart.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
