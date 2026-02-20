# Cart CRUD repository -- manages shopping cart lifecycle for event ticket purchases.
# Handles cart creation/expiry, adding/updating/removing items, seat locking,
# cart validation before checkout, and automatic cleanup of expired carts.

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
# Seats are locked for a shorter window than the cart to reduce blocking other users.
SEAT_LOCK_MINUTES = 7


class CartCRUDRepository(BaseCRUDRepository):

    # Returns the user's active cart for a specific event, or creates a new one.
    # Automatically expires any old carts for the same user+event combination first.
    # If the found cart has expired, it is marked expired and seats are released.
    async def get_or_create_cart(
        self,
        user_id: int,
        event_id: int,
    ) -> Cart:
        """Get active cart for user+event, or create a new one."""
        # First expire any old carts for this user+event
        await self._expire_old_carts(user_id, event_id)

        # Look for existing active cart with eager-loaded items and event.
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

        # Return the cart if it exists and has not expired.
        if cart and not cart.is_expired:
            return cart

        # If expired, mark it and release any locked seats.
        if cart and cart.is_expired:
            cart.status = "expired"
            await self._release_cart_seats(cart)

        # Create new cart with a fresh expiry window.
        now = datetime.datetime.now(datetime.timezone.utc)
        new_cart = Cart(
            user_id=user_id,
            event_id=event_id,
            status="active",
            expires_at=now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES),
        )
        self.async_session.add(new_cart)
        # Flush to get the generated cart ID without committing the transaction.
        await self.async_session.flush()

        # Reload with relationships
        return await self._load_cart(new_cart.id)

    # Adds a seat category item to the cart. For assigned seating, locks specific
    # seats in the database. Validates that the category belongs to the event,
    # is not already in the cart, and has enough available seats.
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
        # Check expiry and auto-expire if needed.
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
        # Prevents duplicate category entries -- user should update quantity instead.
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
            # Verify each requested seat is available and belongs to the correct category,
            # then lock it to prevent other users from selecting it during checkout.
            for seat_id in item_data.seat_ids:
                seat_stmt = sqlalchemy.select(Seat).where(Seat.id == seat_id)
                seat_result = await self.async_session.execute(seat_stmt)
                seat = seat_result.scalar_one_or_none()
                if not seat or not seat.is_available:
                    raise ValueError(f"Seat {seat_id} is not available")
                if seat.category_id != item_data.seat_category_id:
                    raise ValueError(f"Seat {seat_id} does not belong to the selected category")

                # Lock the seat with an expiry time and the locking user's ID.
                seat.status = SeatStatus.LOCKED.value
                seat.locked_until = lock_until
                seat.locked_by = user_id

            seat_ids = item_data.seat_ids

        # Create cart item -- quantity is derived from seat_ids count for assigned seating.
        cart_item = CartItem(
            cart_id=cart_id,
            seat_category_id=item_data.seat_category_id,
            seat_ids=seat_ids,
            quantity=len(item_data.seat_ids) if item_data.seat_ids else item_data.quantity,
            unit_price=category.price,
            locked_until=lock_until if seat_ids else None,
        )
        self.async_session.add(cart_item)

        # Extend cart expiry on every add to give the user more time.
        cart.expires_at = now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES)
        cart.updated_at = now

        await self.async_session.commit()
        return await self._load_cart(cart_id)

    # Updates the quantity of a general admission cart item.
    # Assigned seating items (with seat_ids) cannot have their quantity changed --
    # the user must remove and re-add to select different seats.
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

        # Assigned seating items track specific seats; changing quantity is not meaningful.
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
        # Extend cart expiry on update to give the user more time.
        cart.expires_at = now + datetime.timedelta(minutes=CART_EXPIRY_MINUTES)

        await self.async_session.commit()
        return await self._load_cart(cart_id)

    # Removes an item from the cart and releases any locked seats back to AVAILABLE.
    # Only releases seats that were locked by the requesting user.
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
        # Only release if the seat was locked by this user (safety check).
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

    # Validates the cart before checkout. Checks that the cart is active, not expired,
    # not empty, the event is still bookable, and each item's seats are still available.
    # Returns a tuple of (is_valid, errors, warnings) to inform the checkout flow.
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
                # For assigned seating, verify each specific seat is still held.
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
                # For general admission, just verify enough seats remain in the category.
                cat_stmt = sqlalchemy.select(SeatCategory).where(SeatCategory.id == item.seat_category_id)
                cat_result = await self.async_session.execute(cat_stmt)
                category = cat_result.scalar_one_or_none()
                if category and category.available_seats < item.quantity:
                    errors.append(f"Only {category.available_seats} seats available in {category.name}")

        return len(errors) == 0, errors, warnings

    # Retrieves the user's most recently updated active cart.
    # If the cart has expired, it is automatically marked expired and None is returned.
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

        # Auto-expire and clean up if the cart has passed its expiry time.
        if cart and cart.is_expired:
            cart.status = "expired"
            await self._release_cart_seats(cart)
            await self.async_session.commit()
            return None

        return cart

    # Returns the total number of items (sum of quantities) across all active,
    # non-expired carts for a user. Useful for displaying a cart badge count.
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

    # Loads a cart by ID with all relationships (items, seat categories, event) eager-loaded.
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

    # Finds and expires all carts for a user+event that have passed their expiry time.
    # Releases locked seats for each expired cart and flushes changes.
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

    # Iterates through all items in a cart and releases any locked seats back to AVAILABLE.
    # Only releases seats that are currently in LOCKED status to avoid touching booked seats.
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

    # Allows a user to explicitly abandon their cart, releasing all locked seats
    # and marking the cart as "abandoned" (distinct from "expired").
    async def abandon_cart(self, cart_id: int, user_id: int) -> None:
        """Abandon/clear a cart and release all locked seats."""
        cart = await self._load_cart(cart_id)
        if not cart:
            return

        # Ownership check to prevent users from abandoning other users' carts.
        if cart.user_id != user_id:
            raise ValueError("Cannot abandon another user's cart")

        # Release any locked seats
        await self._release_cart_seats(cart)

        # Mark cart as abandoned
        cart.status = "abandoned"
        cart.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
