# OTP CRUD repository for creating, validating, and managing one-time password codes
import datetime
import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.otp import OTPCode, OTPPurpose
from src.repository.crud.base import BaseCRUDRepository
from src.utilities.exceptions.database import EntityDoesNotExist


class OTPCRUDRepository(BaseCRUDRepository):
    # Creates a new OTP record in the database with the given code, purpose, and expiration
    # Can be linked to a user_id, phone number, or email address
    async def create_otp(
        self,
        code: str,
        purpose: str,
        expires_at: datetime.datetime,
        user_id: int | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> OTPCode:
        """Create a new OTP code"""
        new_otp = OTPCode(
            user_id=user_id,
            phone=phone,
            email=email,
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )

        self.async_session.add(instance=new_otp)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_otp)

        return new_otp

    # Retrieves a valid OTP that matches the code, purpose, and contact method (phone/email)
    # Only returns OTPs that have not been used and have not expired
    # Orders by newest first to get the most recent matching OTP
    async def get_valid_otp(
        self,
        code: str,
        purpose: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> OTPCode | None:
        """Get a valid (not used, not expired) OTP code"""
        now = datetime.datetime.now(datetime.timezone.utc)

        stmt = sqlalchemy.select(OTPCode).where(
            OTPCode.code == code,
            OTPCode.purpose == purpose,
            OTPCode.is_used == False,
            OTPCode.expires_at > now,
        )

        # Filter by the delivery method used
        if phone:
            stmt = stmt.where(OTPCode.phone == phone)
        if email:
            stmt = stmt.where(OTPCode.email == email)

        # Get the most recently created matching OTP
        stmt = stmt.order_by(OTPCode.created_at.desc())

        query = await self.async_session.execute(statement=stmt)
        return query.scalar()

    # Marks a specific OTP as used so it cannot be reused
    async def mark_otp_as_used(self, otp_id: int) -> None:
        """Mark an OTP code as used"""
        stmt = (
            sqlalchemy.update(OTPCode)
            .where(OTPCode.id == otp_id)
            .values(is_used=True)
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Invalidates all previous unused OTPs for the same purpose and contact method
    # Called before creating a new OTP to ensure only the latest code is valid
    async def invalidate_previous_otps(
        self,
        purpose: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> None:
        """Invalidate all previous unused OTPs for the same purpose and phone/email"""
        stmt = (
            sqlalchemy.update(OTPCode)
            .where(
                OTPCode.purpose == purpose,
                OTPCode.is_used == False,
            )
            .values(is_used=True)
        )

        if phone:
            stmt = stmt.where(OTPCode.phone == phone)
        if email:
            stmt = stmt.where(OTPCode.email == email)

        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Deletes all expired OTP records from the database as a cleanup/maintenance task
    # Returns the number of deleted rows
    async def cleanup_expired_otps(self) -> int:
        """Delete expired OTP codes (cleanup task)"""
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = sqlalchemy.delete(OTPCode).where(OTPCode.expires_at < now)
        result = await self.async_session.execute(statement=stmt)
        await self.async_session.commit()
        return result.rowcount  # type: ignore
