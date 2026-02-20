# Account CRUD repository for all database operations related to user accounts
import datetime
import typing

import sqlalchemy
from sqlalchemy.sql import functions as sqlalchemy_functions

from src.models.db.account import Account, UserRole
from src.models.schemas.account import AccountInCreate, AccountInLogin, AccountInUpdate, AccountProfileUpdate
from src.repository.crud.base import BaseCRUDRepository
from src.securities.hashing.password import pwd_generator
from src.securities.verifications.credentials import credential_verifier
from src.utilities.exceptions.database import EntityAlreadyExists, EntityDoesNotExist
from src.utilities.exceptions.password import PasswordDoesNotMatch


class AccountCRUDRepository(BaseCRUDRepository):
    # Creates a new user account with hashed password and salt, then persists it to the database
    async def create_account(
        self,
        account_create: AccountInCreate,
        role: str = UserRole.USER.value,
    ) -> Account:
        new_account = Account(
            username=account_create.username,
            email=account_create.email,
            phone=account_create.phone,
            full_name=account_create.full_name,
            role=role,
            is_logged_in=True,
        )

        # Generate a unique salt and hash the password before storing
        new_account.set_hash_salt(hash_salt=pwd_generator.generate_salt)
        new_account.set_hashed_password(
            hashed_password=pwd_generator.generate_hashed_password(
                hash_salt=new_account.hash_salt, new_password=account_create.password
            )
        )

        self.async_session.add(instance=new_account)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_account)

        return new_account

    # Retrieves all accounts from the database (no pagination)
    async def read_accounts(self) -> typing.Sequence[Account]:
        stmt = sqlalchemy.select(Account)
        query = await self.async_session.execute(statement=stmt)
        return query.scalars().all()

    # Fetches a single account by its primary key ID
    async def read_account_by_id(self, id: int) -> Account:
        stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist("Account with id `{id}` does not exist!")

        return query.scalar()  # type: ignore

    # Fetches a single account by its unique username
    async def read_account_by_username(self, username: str) -> Account:
        stmt = sqlalchemy.select(Account).where(Account.username == username)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist("Account with username `{username}` does not exist!")

        return query.scalar()  # type: ignore

    # Fetches a single account by its unique email address
    async def read_account_by_email(self, email: str) -> Account:
        stmt = sqlalchemy.select(Account).where(Account.email == email)
        query = await self.async_session.execute(statement=stmt)

        if not query:
            raise EntityDoesNotExist("Account with email `{email}` does not exist!")

        return query.scalar()  # type: ignore

    # Authenticates a user by matching username+email and verifying the password hash
    # Raises EntityDoesNotExist if credentials don't match, PasswordDoesNotMatch if password is wrong
    async def read_user_by_password_authentication(self, account_login: AccountInLogin) -> Account:
        stmt = sqlalchemy.select(Account).where(
            Account.username == account_login.username, Account.email == account_login.email
        )
        query = await self.async_session.execute(statement=stmt)
        db_account = query.scalar()

        if not db_account:
            raise EntityDoesNotExist("Wrong username or wrong email!")

        if not pwd_generator.is_password_authenticated(hash_salt=db_account.hash_salt, password=account_login.password, hashed_password=db_account.hashed_password):  # type: ignore
            raise PasswordDoesNotMatch("Password does not match!")

        return db_account  # type: ignore

    # Updates an account by ID with partial data; re-hashes password if it changes
    async def update_account_by_id(self, id: int, account_update: AccountInUpdate) -> Account:
        new_account_data = account_update.dict()

        select_stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=select_stmt)
        update_account = query.scalar()

        if not update_account:
            raise EntityDoesNotExist(f"Account with id `{id}` does not exist!")  # type: ignore

        update_stmt = sqlalchemy.update(table=Account).where(Account.id == update_account.id).values(updated_at=sqlalchemy_functions.now())  # type: ignore

        if new_account_data["username"]:
            update_stmt = update_stmt.values(username=new_account_data["username"])

        if new_account_data["email"]:
            update_stmt = update_stmt.values(username=new_account_data["email"])

        # If password is being changed, generate new salt and hash
        if new_account_data["password"]:
            update_account.set_hash_salt(hash_salt=pwd_generator.generate_salt)  # type: ignore
            update_account.set_hashed_password(hashed_password=pwd_generator.generate_hashed_password(hash_salt=update_account.hash_salt, new_password=new_account_data["password"]))  # type: ignore

        await self.async_session.execute(statement=update_stmt)
        await self.async_session.commit()
        await self.async_session.refresh(instance=update_account)

        return update_account  # type: ignore

    # Permanently deletes an account by ID; raises EntityDoesNotExist if not found
    async def delete_account_by_id(self, id: int) -> str:
        select_stmt = sqlalchemy.select(Account).where(Account.id == id)
        query = await self.async_session.execute(statement=select_stmt)
        delete_account = query.scalar()

        if not delete_account:
            raise EntityDoesNotExist(f"Account with id `{id}` does not exist!")  # type: ignore

        stmt = sqlalchemy.delete(table=Account).where(Account.id == delete_account.id)

        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return f"Account with id '{id}' is successfully deleted!"

    # Checks if a username is already taken; raises EntityAlreadyExists if so
    async def is_username_taken(self, username: str) -> bool:
        username_stmt = sqlalchemy.select(Account.username).select_from(Account).where(Account.username == username)
        username_query = await self.async_session.execute(username_stmt)
        db_username = username_query.scalar()

        if not credential_verifier.is_username_available(username=db_username):
            raise EntityAlreadyExists(f"The username `{username}` is already taken!")  # type: ignore

        return True

    # Checks if an email is already registered; raises EntityAlreadyExists if so
    async def is_email_taken(self, email: str) -> bool:
        email_stmt = sqlalchemy.select(Account.email).select_from(Account).where(Account.email == email)
        email_query = await self.async_session.execute(email_stmt)
        db_email = email_query.scalar()

        if not credential_verifier.is_email_available(email=db_email):
            raise EntityAlreadyExists(f"The email `{email}` is already registered!")  # type: ignore

        return True

    # ==================== Email OTP methods ====================

    # Generates a unique username from the email's local part with a random numeric suffix
    # Retries up to 10 times with random suffixes, then falls back to a UUID-based suffix
    async def generate_unique_username(self, email: str) -> str:
        """Generate a unique username from email prefix + random suffix."""
        import random
        import re

        local_part = email.split("@")[0]
        local_part = re.sub(r'[^a-zA-Z0-9_]', '', local_part)

        if not local_part:
            local_part = "user"

        local_part = local_part[:50]

        for _ in range(10):
            suffix = str(random.randint(1000, 9999))
            candidate = f"{local_part}_{suffix}"

            stmt = sqlalchemy.select(Account.username).where(Account.username == candidate)
            result = await self.async_session.execute(statement=stmt)
            if result.scalar() is None:
                return candidate

        import uuid
        return f"{local_part}_{uuid.uuid4().hex[:8]}"

    # Creates a new account for email-OTP based signup (no password required)
    # The account is immediately marked as verified and active
    async def create_account_from_email_otp(self, email: str, username: str) -> Account:
        """Create a new account for email-OTP signup (no password)."""
        new_account = Account(
            username=username,
            email=email,
            role=UserRole.USER.value,
            is_verified=True,
            is_active=True,
            is_logged_in=True,
        )

        self.async_session.add(instance=new_account)
        await self.async_session.commit()
        await self.async_session.refresh(instance=new_account)

        return new_account

    # ==================== New methods for Phase 1 ====================

    # Looks up an account by phone number; returns None if not found
    async def read_account_by_phone(self, phone: str) -> Account | None:
        """Get account by phone number"""
        stmt = sqlalchemy.select(Account).where(Account.phone == phone)
        query = await self.async_session.execute(statement=stmt)
        return query.scalar()

    # Updates the last_login_at timestamp and sets is_logged_in to True
    async def update_last_login(self, account_id: int) -> Account:
        """Update last login timestamp and return refreshed account"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(
                last_login_at=sqlalchemy_functions.now(),
                is_logged_in=True,
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()
        return await self.read_account_by_id(id=account_id)

    # Updates user profile fields (username, email, phone, full_name) that are provided
    # Skips the update if no fields are provided and returns the current account
    async def update_profile(self, account_id: int, profile_update: AccountProfileUpdate) -> Account:
        """Update user profile"""
        update_data = profile_update.dict(exclude_unset=True, exclude_none=True)

        if not update_data:
            # Nothing to update, return current account
            return await self.read_account_by_id(id=account_id)

        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(**update_data, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_account_by_id(id=account_id)

    # Marks the user's phone number as verified in the database
    async def verify_phone(self, account_id: int) -> None:
        """Mark phone as verified"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(is_phone_verified=True, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Marks the user's email address as verified in the database
    async def verify_email(self, account_id: int) -> None:
        """Mark email as verified"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(is_verified=True, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # Updates the user's password by generating a new salt and hashing the new password
    async def update_password(self, account_id: int, new_password: str) -> None:
        """Update user password"""
        account = await self.read_account_by_id(id=account_id)
        if not account:
            raise EntityDoesNotExist(f"Account with id `{account_id}` does not exist!")

        new_salt = pwd_generator.generate_salt
        new_hashed_password = pwd_generator.generate_hashed_password(
            hash_salt=new_salt, new_password=new_password
        )

        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(
                _hash_salt=new_salt,
                _hashed_password=new_hashed_password,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

    # ==================== Admin methods ====================

    # Retrieves a paginated list of accounts with optional search filtering
    # Searches across username, email, and full_name fields using case-insensitive LIKE
    async def read_accounts_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[typing.Sequence[Account], int]:
        """Get accounts with pagination and search (for admin)"""
        stmt = sqlalchemy.select(Account)

        # Apply search filter across username, email, and full_name
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                sqlalchemy.or_(
                    Account.username.ilike(search_pattern),
                    Account.email.ilike(search_pattern),
                    Account.full_name.ilike(search_pattern),
                )
            )

        # Count total matching records before pagination
        count_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(stmt.subquery())
        count_result = await self.async_session.execute(statement=count_stmt)
        total = count_result.scalar() or 0

        # Order by newest first and apply offset/limit pagination
        stmt = stmt.order_by(Account.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        query = await self.async_session.execute(statement=stmt)
        accounts = query.scalars().all()

        return accounts, total

    # Blocks a user account with an optional reason; prevents the user from logging in
    async def block_user(self, account_id: int, reason: str | None = None) -> Account:
        """Block a user account"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(
                is_blocked=True,
                blocked_reason=reason,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_account_by_id(id=account_id)

    # Unblocks a previously blocked user account and clears the blocked reason
    async def unblock_user(self, account_id: int) -> Account:
        """Unblock a user account"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(
                is_blocked=False,
                blocked_reason=None,
                updated_at=sqlalchemy_functions.now(),
            )
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_account_by_id(id=account_id)

    # Promotes a regular user to admin role
    async def make_admin(self, account_id: int) -> Account:
        """Promote a user to admin"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(role=UserRole.ADMIN.value, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_account_by_id(id=account_id)

    # Demotes an admin back to a regular user role
    async def remove_admin(self, account_id: int) -> Account:
        """Demote an admin to regular user"""
        stmt = (
            sqlalchemy.update(Account)
            .where(Account.id == account_id)
            .values(role=UserRole.USER.value, updated_at=sqlalchemy_functions.now())
        )
        await self.async_session.execute(statement=stmt)
        await self.async_session.commit()

        return await self.read_account_by_id(id=account_id)

    # Gathers aggregate statistics about user accounts for the admin dashboard
    # Runs multiple COUNT queries for total, active, blocked, admin, today's, and this week's users
    async def get_stats(self) -> dict:
        """Get user statistics for admin dashboard"""
        # Total users
        total_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account)
        total_result = await self.async_session.execute(statement=total_stmt)
        total_users = total_result.scalar() or 0

        # Active users (not blocked)
        active_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account).where(
            Account.is_blocked == False
        )
        active_result = await self.async_session.execute(statement=active_stmt)
        active_users = active_result.scalar() or 0

        # Blocked users
        blocked_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account).where(
            Account.is_blocked == True
        )
        blocked_result = await self.async_session.execute(statement=blocked_stmt)
        blocked_users = blocked_result.scalar() or 0

        # Admin users
        admin_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account).where(
            Account.role == UserRole.ADMIN.value
        )
        admin_result = await self.async_session.execute(statement=admin_stmt)
        admin_users = admin_result.scalar() or 0

        # New users registered today (from midnight UTC)
        today_start = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account).where(
            Account.created_at >= today_start
        )
        today_result = await self.async_session.execute(statement=today_stmt)
        new_users_today = today_result.scalar() or 0

        # New users registered in the last 7 days
        seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        week_stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(Account).where(
            Account.created_at >= seven_days_ago
        )
        week_result = await self.async_session.execute(statement=week_stmt)
        new_users_week = week_result.scalar() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "admin_users": admin_users,
            "new_users_today": new_users_today,
            "new_users_week": new_users_week,
        }
