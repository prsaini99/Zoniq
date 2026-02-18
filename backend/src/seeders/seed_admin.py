"""
Admin Seeder

This script creates the initial admin user on first startup.
Can be run manually or called from application startup.

Usage:
    python -m src.seeders.seed_admin

Environment variables:
    ADMIN_EMAIL: Admin email (default: admin@zoniq.com)
    ADMIN_PASSWORD: Admin password (default: admin123!)
    ADMIN_USERNAME: Admin username (default: admin)
"""

import asyncio
import os
import sys

import decouple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import src.models.db  # noqa: F401 — import all models so relationships resolve
from src.models.db.account import Account, UserRole
from src.securities.hashing.password import pwd_generator
from src.repository.database import async_db


async def create_admin_user(async_session: AsyncSession) -> Account | None:
    """Create the initial admin user if it doesn't exist"""

    # Get admin credentials from environment
    admin_email = decouple.config("ADMIN_EMAIL", default="admin@zoniq.com", cast=str)
    admin_password = decouple.config("ADMIN_PASSWORD", default="admin123!", cast=str)
    admin_username = decouple.config("ADMIN_USERNAME", default="admin", cast=str)

    # Check if admin already exists
    stmt = select(Account).where(
        (Account.email == admin_email) | (Account.username == admin_username)
    )
    result = await async_session.execute(stmt)
    existing_admin = result.scalar()

    if existing_admin:
        logger.info(f"Admin user already exists: {existing_admin.username} ({existing_admin.email})")
        return existing_admin

    # Create admin user
    admin = Account(
        username=admin_username,
        email=admin_email,
        role=UserRole.ADMIN.value,
        is_verified=True,
        is_active=True,
        is_logged_in=False,
    )

    # Set password
    admin.set_hash_salt(hash_salt=pwd_generator.generate_salt)
    admin.set_hashed_password(
        hashed_password=pwd_generator.generate_hashed_password(
            hash_salt=admin.hash_salt, new_password=admin_password
        )
    )

    async_session.add(admin)
    await async_session.commit()
    await async_session.refresh(admin)

    logger.info(f"Admin user created successfully: {admin_username} ({admin_email})")
    logger.warning("IMPORTANT: Change the default admin password immediately!")

    return admin


async def seed_admin():
    """Main seeder function"""
    logger.info("Starting admin seeder...")

    try:
        async with async_db.async_session as session:
            await create_admin_user(async_session=session)
    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")
        raise


async def seed_admin_on_startup(async_session: AsyncSession):
    """
    Called from application startup to ensure admin exists.
    This is a safe operation that won't create duplicates.
    """
    try:
        await create_admin_user(async_session=async_session)
    except Exception as e:
        logger.error(f"Failed to seed admin user on startup: {e}")
        # Don't raise - app should still start even if seeding fails


if __name__ == "__main__":
    asyncio.run(seed_admin())
