# Cart routes: manage shopping cart for event ticket purchases
# All endpoints require authentication (get_current_user dependency)
# The cart holds items (seat selections) before they are converted into a booking at checkout
import fastapi
from fastapi import Depends, HTTPException
from decimal import Decimal

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.cart import (
    CartCreate,
    CartAddItem,
    CartUpdateItem,
    CheckoutRequest,
    CartResponse,
    CartItemResponse,
    CartValidationResponse,
)
from src.models.schemas.booking import BookingDetailResponse, BookingItemResponse, BookingEventInfo
from src.repository.crud.cart import CartCRUDRepository
from src.repository.crud.booking import BookingCRUDRepository

# All cart routes are grouped under the /cart prefix
router = fastapi.APIRouter(prefix="/cart", tags=["cart"])


def _build_cart_response(cart) -> CartResponse:
    """Build a CartResponse from a Cart model instance."""
    items = []
    subtotal = Decimal("0")

    # Iterate over each cart item, compute per-item subtotals, and accumulate the cart subtotal
    for item in cart.items:
        item_subtotal = Decimal(str(item.unit_price)) * item.quantity
        subtotal += item_subtotal
        items.append(CartItemResponse(
            id=item.id,
            seat_category_id=item.seat_category_id,
            category_name=item.seat_category.name if item.seat_category else None,
            category_color=item.seat_category.color_code if item.seat_category else None,
            seat_ids=item.seat_ids,
            quantity=item.quantity,
            unit_price=item.unit_price,
            subtotal=item_subtotal,
            locked_until=item.locked_until,
        ))

    # Total equals subtotal (no discount/tax logic at cart level)
    total = subtotal
    # Total ticket count across all items
    item_count = sum(item.quantity for item in cart.items)

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        event_id=cart.event_id,
        event_title=cart.event.title if cart.event else None,
        event_date=cart.event.event_date if cart.event else None,
        event_image=cart.event.thumbnail_image_url or (cart.event.banner_image_url if cart.event else None),
        status=cart.status,
        items=items,
        subtotal=subtotal,
        total=total,
        item_count=item_count,
        expires_at=cart.expires_at,
    )


# POST /cart - Get the user's existing active cart for an event, or create a new one
@router.post(
    "",
    name="cart:get-or-create",
    response_model=CartResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_or_create_cart(
    cart_data: CartCreate,
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartResponse:
    """Get or create an active cart for the user and event."""
    # Idempotent: returns existing active cart or creates a fresh one
    cart = await cart_repo.get_or_create_cart(
        user_id=current_user.id,
        event_id=cart_data.event_id,
    )
    return _build_cart_response(cart)


# POST /cart/items - Add a seat category selection to the cart
@router.post(
    "/items",
    name="cart:add-item",
    response_model=CartResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def add_item_to_cart(
    item_data: CartAddItem,
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartResponse:
    """Add an item to the cart. Creates a cart if none exists."""
    # Ensure the user has an active cart for this event
    cart = await cart_repo.get_or_create_cart(
        user_id=current_user.id,
        event_id=item_data.event_id,
    )

    # Add the item; this may lock seats and validate availability
    try:
        cart = await cart_repo.add_item(
            cart_id=cart.id,
            item_data=item_data,
            user_id=current_user.id,
        )
    except ValueError as e:
        # ValueError indicates a business rule violation (e.g., seat unavailable, max tickets exceeded)
        raise HTTPException(status_code=400, detail=str(e))

    return _build_cart_response(cart)


# PATCH /cart/items/{item_id} - Update the quantity of an existing cart item
@router.patch(
    "/items/{item_id}",
    name="cart:update-item",
    response_model=CartResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_cart_item(
    item_id: int,
    update_data: CartUpdateItem,
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartResponse:
    """Update quantity of a cart item."""
    # Look up the user's current active cart (not tied to a specific event here)
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found")

    # Apply the quantity update; may re-validate seat locks
    try:
        cart = await cart_repo.update_item(
            cart_id=cart.id,
            item_id=item_id,
            update_data=update_data,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_cart_response(cart)


# DELETE /cart/items/{item_id} - Remove an item from the cart and release its locked seats
@router.delete(
    "/items/{item_id}",
    name="cart:remove-item",
    response_model=CartResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def remove_cart_item(
    item_id: int,
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartResponse:
    """Remove an item from the cart and release locked seats."""
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found")

    # Remove the item and release any seat locks held by it
    try:
        cart = await cart_repo.remove_item(
            cart_id=cart.id,
            item_id=item_id,
            user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _build_cart_response(cart)


# GET /cart/validate - Pre-checkout validation to ensure all cart items are still valid
@router.get(
    "/validate",
    name="cart:validate",
    response_model=CartValidationResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def validate_cart(
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartValidationResponse:
    """Validate the cart before checkout."""
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if not cart:
        return CartValidationResponse(is_valid=False, errors=["No active cart found"])

    # Check seat locks, availability, pricing, and business rules
    is_valid, errors, warnings = await cart_repo.validate_cart(cart_id=cart.id)
    return CartValidationResponse(is_valid=is_valid, errors=errors, warnings=warnings)


# POST /cart/checkout - Convert the cart into a confirmed booking
@router.post(
    "/checkout",
    name="cart:checkout",
    response_model=BookingDetailResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def checkout(
    checkout_data: CheckoutRequest,
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
    booking_repo: BookingCRUDRepository = Depends(get_repository(repo_type=BookingCRUDRepository)),
) -> BookingDetailResponse:
    """Convert the cart into a booking (checkout)."""
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found")

    # Step 1: Validate the cart before proceeding to ensure seats are still available
    is_valid, errors, warnings = await cart_repo.validate_cart(cart_id=cart.id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Cart validation failed: {'; '.join(errors)}")

    # Step 2: Atomically create a booking from the cart contents
    # Uses checkout contact info or falls back to the user's account email/phone
    try:
        booking = await booking_repo.create_booking_from_cart(
            cart=cart,
            user_id=current_user.id,
            contact_email=checkout_data.contact_email or current_user.email,
            contact_phone=checkout_data.contact_phone or current_user.phone,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Checkout failed: {str(e)}")

    # Step 3: Build the booking detail response with event and venue information
    event_info = None
    if booking.event:
        venue_name = None
        venue_city = None
        if booking.event.venue:
            venue_name = booking.event.venue.name
            venue_city = booking.event.venue.city

        event_info = BookingEventInfo(
            id=booking.event.id,
            title=booking.event.title,
            slug=booking.event.slug,
            event_date=booking.event.event_date,
            banner_image_url=booking.event.banner_image_url,
            thumbnail_image_url=booking.event.thumbnail_image_url,
            venue_name=venue_name,
            venue_city=venue_city,
        )

    # Map each booking item (ticket) to its response schema
    items = [
        BookingItemResponse(
            id=item.id,
            booking_id=item.booking_id,
            seat_id=item.seat_id,
            category_id=item.category_id,
            category_name=item.category_name,
            seat_label=item.seat_label,
            price=item.price,
            ticket_number=item.ticket_number,
            is_used=item.is_used,
            used_at=item.used_at,
        )
        for item in booking.items
    ]

    return BookingDetailResponse(
        id=booking.id,
        booking_number=booking.booking_number,
        user_id=booking.user_id,
        event_id=booking.event_id,
        event=event_info,
        status=booking.status,
        total_amount=booking.total_amount,
        discount_amount=booking.discount_amount,
        final_amount=booking.final_amount,
        payment_status=booking.payment_status,
        promo_code_used=booking.promo_code_used,
        ticket_count=booking.ticket_count,
        contact_email=booking.contact_email,
        contact_phone=booking.contact_phone,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        items=items,
    )


# GET /cart/current - Retrieve the user's active cart without creating a new one
@router.get(
    "/current",
    name="cart:current",
    response_model=CartResponse | None,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_current_cart(
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> CartResponse | None:
    """Get the user's current active cart (if any)."""
    # Returns None if no active cart exists (does not create one)
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if not cart:
        return None
    return _build_cart_response(cart)


# DELETE /cart/clear - Abandon the user's active cart and release all locked seats
@router.delete(
    "/clear",
    name="cart:clear",
    status_code=fastapi.status.HTTP_200_OK,
)
async def clear_cart(
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> dict:
    """Clear/abandon the user's current active cart and release any locked seats."""
    cart = await cart_repo.get_user_active_cart(user_id=current_user.id)
    if cart:
        # Mark the cart as abandoned and release all seat locks
        await cart_repo.abandon_cart(cart_id=cart.id, user_id=current_user.id)
    return {"success": True, "message": "Cart cleared"}


# GET /cart/count - Return the total number of items across the user's active carts
@router.get(
    "/count",
    name="cart:count",
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_cart_count(
    current_user: Account = Depends(get_current_user),
    cart_repo: CartCRUDRepository = Depends(get_repository(repo_type=CartCRUDRepository)),
) -> dict:
    """Get the total item count in the user's active carts."""
    # Useful for displaying a badge count in the UI header
    count = await cart_repo.get_cart_count(user_id=current_user.id)
    return {"count": count}
