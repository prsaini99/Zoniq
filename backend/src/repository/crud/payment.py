import datetime

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession as SQLAlchemyAsyncSession

from src.models.db.payment import Payment
from src.models.db.booking import Booking
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class PaymentCRUDRepository(BaseCRUDRepository):
    """
    CRUD operations for Payment model.
    """

    async def create_payment(
        self,
        booking_id: int,
        user_id: int,
        razorpay_order_id: str,
        amount: int,
        currency: str = "INR",
    ) -> Payment:
        """Create a new payment record."""
        payment = Payment(
            booking_id=booking_id,
            user_id=user_id,
            razorpay_order_id=razorpay_order_id,
            amount=amount,
            currency=currency,
            status="created",
        )
        self.async_session.add(payment)
        await self.async_session.commit()
        await self.async_session.refresh(payment)
        return payment

    async def read_payment_by_id(self, payment_id: int) -> Payment:
        """Get a payment by ID."""
        stmt = sqlalchemy.select(Payment).where(Payment.id == payment_id)
        result = await self.async_session.execute(stmt)
        payment = result.scalar_one_or_none()
        if not payment:
            raise EntityDoesNotExist(f"Payment with id {payment_id} does not exist")
        return payment

    async def read_payment_by_order_id(self, razorpay_order_id: str) -> Payment:
        """Get a payment by Razorpay order ID."""
        stmt = sqlalchemy.select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        result = await self.async_session.execute(stmt)
        payment = result.scalar_one_or_none()
        if not payment:
            raise EntityDoesNotExist(f"Payment with order_id {razorpay_order_id} does not exist")
        return payment

    async def read_payment_by_booking_id(self, booking_id: int) -> Payment | None:
        """Get a payment by booking ID (may return None if no payment exists)."""
        stmt = (
            sqlalchemy.select(Payment)
            .where(Payment.booking_id == booking_id)
            .order_by(Payment.created_at.desc())
        )
        result = await self.async_session.execute(stmt)
        return result.scalar_one_or_none()

    async def read_payments_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Payment], int]:
        """Get payments for a user with pagination."""
        # Count total
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(Payment)
            .where(Payment.user_id == user_id)
        )
        count_result = await self.async_session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            sqlalchemy.select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.async_session.execute(stmt)
        payments = list(result.scalars().all())

        return payments, total

    async def update_payment_success(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        method: str | None = None,
    ) -> Payment:
        """Update payment record after successful payment."""
        payment = await self.read_payment_by_order_id(razorpay_order_id)

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "captured"
        payment.method = method
        payment.paid_at = datetime.datetime.now(datetime.timezone.utc)

        # Also update the booking
        stmt = sqlalchemy.select(Booking).where(Booking.id == payment.booking_id)
        result = await self.async_session.execute(stmt)
        booking = result.scalar_one_or_none()
        if booking:
            booking.payment_status = "success"
            booking.payment_id = razorpay_payment_id
            booking.status = "confirmed"
            booking.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
        await self.async_session.refresh(payment)
        return payment

    async def update_payment_failed(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str | None = None,
        error_code: str | None = None,
        error_description: str | None = None,
    ) -> Payment:
        """Update payment record after failed payment."""
        payment = await self.read_payment_by_order_id(razorpay_order_id)

        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "failed"
        payment.error_code = error_code
        payment.error_description = error_description

        # Also update the booking
        stmt = sqlalchemy.select(Booking).where(Booking.id == payment.booking_id)
        result = await self.async_session.execute(stmt)
        booking = result.scalar_one_or_none()
        if booking:
            booking.payment_status = "failed"
            booking.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
        await self.async_session.refresh(payment)
        return payment

    async def update_payment_refund(
        self,
        payment_id: int,
        refund_id: str,
        refund_amount: int,
        refund_status: str = "processed",
    ) -> Payment:
        """Update payment record after refund."""
        payment = await self.read_payment_by_id(payment_id)

        payment.refund_id = refund_id
        payment.refund_amount = refund_amount
        payment.refund_status = refund_status
        payment.refunded_at = datetime.datetime.now(datetime.timezone.utc)

        if refund_amount >= payment.amount:
            payment.status = "refunded"

        # Also update the booking
        stmt = sqlalchemy.select(Booking).where(Booking.id == payment.booking_id)
        result = await self.async_session.execute(stmt)
        booking = result.scalar_one_or_none()
        if booking:
            if refund_amount >= payment.amount:
                booking.payment_status = "refunded"
                booking.status = "refunded"
            booking.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
        await self.async_session.refresh(payment)
        return payment
