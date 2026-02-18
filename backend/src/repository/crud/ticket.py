import datetime
import secrets

import sqlalchemy
from sqlalchemy.orm import joinedload

from src.models.db.booking import Booking, BookingItem
from src.models.db.ticket_transfer import TicketTransfer
from src.models.db.account import Account
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class TicketCRUDRepository(BaseCRUDRepository):
    """
    CRUD operations for Tickets (BookingItem) and Transfers.
    """

    async def read_ticket_by_id(self, ticket_id: int) -> BookingItem:
        """Get a ticket by ID with related data."""
        stmt = (
            sqlalchemy.select(BookingItem)
            .options(
                joinedload(BookingItem.booking).joinedload(Booking.event),
                joinedload(BookingItem.booking).joinedload(Booking.user),
            )
            .where(BookingItem.id == ticket_id)
        )
        result = await self.async_session.execute(stmt)
        ticket = result.unique().scalar_one_or_none()
        if not ticket:
            raise EntityDoesNotExist(f"Ticket with id {ticket_id} does not exist")
        return ticket

    async def read_ticket_by_number(self, ticket_number: str) -> BookingItem:
        """Get a ticket by ticket number with related data."""
        stmt = (
            sqlalchemy.select(BookingItem)
            .options(
                joinedload(BookingItem.booking).joinedload(Booking.event),
                joinedload(BookingItem.booking).joinedload(Booking.user),
            )
            .where(BookingItem.ticket_number == ticket_number)
        )
        result = await self.async_session.execute(stmt)
        ticket = result.unique().scalar_one_or_none()
        if not ticket:
            raise EntityDoesNotExist(f"Ticket with number {ticket_number} does not exist")
        return ticket

    async def read_tickets_by_booking(self, booking_id: int) -> list[BookingItem]:
        """Get all tickets for a booking."""
        stmt = (
            sqlalchemy.select(BookingItem)
            .options(
                joinedload(BookingItem.booking).joinedload(Booking.event),
            )
            .where(BookingItem.booking_id == booking_id)
            .order_by(BookingItem.id)
        )
        result = await self.async_session.execute(stmt)
        return list(result.unique().scalars().all())

    async def mark_ticket_used(self, ticket_number: str) -> BookingItem:
        """Mark a ticket as used."""
        ticket = await self.read_ticket_by_number(ticket_number)

        if ticket.is_used:
            raise ValueError(f"Ticket already used at {ticket.used_at}")

        ticket.is_used = True
        ticket.used_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()
        await self.async_session.refresh(ticket)

        return ticket

    async def initiate_transfer(
        self,
        ticket_id: int,
        from_user_id: int,
        to_email: str,
        message: str | None = None,
    ) -> TicketTransfer:
        """Initiate a ticket transfer."""
        ticket = await self.read_ticket_by_id(ticket_id)

        # Verify ownership
        if ticket.booking.user_id != from_user_id:
            raise ValueError("You don't own this ticket")

        # Check if ticket is already used
        if ticket.is_used:
            raise ValueError("Cannot transfer a used ticket")

        # Check if there's already a pending transfer
        stmt = sqlalchemy.select(TicketTransfer).where(
            TicketTransfer.booking_item_id == ticket_id,
            TicketTransfer.status == "pending",
        )
        result = await self.async_session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("There's already a pending transfer for this ticket")

        # Check if recipient exists
        stmt = sqlalchemy.select(Account).where(Account.email == to_email)
        result = await self.async_session.execute(stmt)
        to_user = result.scalar_one_or_none()

        # Generate transfer token
        transfer_token = secrets.token_urlsafe(32)

        # Create transfer record (expires in 48 hours)
        transfer = TicketTransfer(
            booking_item_id=ticket_id,
            from_user_id=from_user_id,
            to_user_id=to_user.id if to_user else None,
            to_email=to_email,
            transfer_token=transfer_token,
            message=message,
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=48),
        )

        self.async_session.add(transfer)
        await self.async_session.commit()
        await self.async_session.refresh(transfer)

        return transfer

    async def claim_transfer(
        self,
        transfer_token: str,
        user_id: int,
        user_email: str,
    ) -> tuple[bool, str, BookingItem | None]:
        """
        Claim a transferred ticket.
        Returns (success, message, ticket).
        """
        # Find the transfer
        stmt = sqlalchemy.select(TicketTransfer).where(
            TicketTransfer.transfer_token == transfer_token
        )
        result = await self.async_session.execute(stmt)
        transfer = result.scalar_one_or_none()

        if not transfer:
            return False, "Transfer not found", None

        if transfer.status != "pending":
            return False, f"Transfer is {transfer.status}", None

        if transfer.expires_at < datetime.datetime.now(datetime.timezone.utc):
            transfer.status = "expired"
            await self.async_session.commit()
            return False, "Transfer has expired", None

        # Verify recipient email matches
        if transfer.to_email.lower() != user_email.lower():
            return False, "This transfer is for a different email address", None

        # Get the ticket
        ticket = await self.read_ticket_by_id(transfer.booking_item_id)

        # Update the booking to new owner
        ticket.booking.user_id = user_id
        ticket.booking.updated_at = datetime.datetime.now(datetime.timezone.utc)

        # Update transfer status
        transfer.status = "completed"
        transfer.to_user_id = user_id
        transfer.transferred_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()

        return True, "Ticket transferred successfully", ticket

    async def cancel_transfer(self, transfer_id: int, user_id: int) -> bool:
        """Cancel a pending transfer."""
        stmt = sqlalchemy.select(TicketTransfer).where(
            TicketTransfer.id == transfer_id
        )
        result = await self.async_session.execute(stmt)
        transfer = result.scalar_one_or_none()

        if not transfer:
            raise EntityDoesNotExist(f"Transfer with id {transfer_id} does not exist")

        if transfer.from_user_id != user_id:
            raise ValueError("You don't own this transfer")

        if transfer.status != "pending":
            raise ValueError(f"Cannot cancel a {transfer.status} transfer")

        transfer.status = "cancelled"
        transfer.cancelled_at = datetime.datetime.now(datetime.timezone.utc)

        await self.async_session.commit()

        return True

    async def read_transfer_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TicketTransfer], int]:
        """Get transfer history for a user (both sent and received)."""
        # Count total
        count_stmt = (
            sqlalchemy.select(sqlalchemy.func.count())
            .select_from(TicketTransfer)
            .where(
                sqlalchemy.or_(
                    TicketTransfer.from_user_id == user_id,
                    TicketTransfer.to_user_id == user_id,
                )
            )
        )
        count_result = await self.async_session.execute(count_stmt)
        total = count_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            sqlalchemy.select(TicketTransfer)
            .options(
                joinedload(TicketTransfer.booking_item),
                joinedload(TicketTransfer.from_user),
                joinedload(TicketTransfer.to_user),
            )
            .where(
                sqlalchemy.or_(
                    TicketTransfer.from_user_id == user_id,
                    TicketTransfer.to_user_id == user_id,
                )
            )
            .order_by(TicketTransfer.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.async_session.execute(stmt)
        transfers = list(result.unique().scalars().all())

        return transfers, total
