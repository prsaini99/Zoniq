# Account schemas for user registration, authentication, profile management, and admin user views
import datetime

import pydantic

from src.models.schemas.base import BaseSchemaModel


# Schema for creating a new user account (registration)
class AccountInCreate(BaseSchemaModel):
    # Required unique username for the account
    username: str
    # Required valid email address
    email: pydantic.EmailStr
    # Required password (will be hashed before storage)
    password: str
    # Optional phone number for contact and OTP verification
    phone: str | None = None
    # Optional display name of the user
    full_name: str | None = None
    # Optional OTP code for email verification during signup
    email_otp_code: str | None = None


# Schema for updating an existing account (all fields optional for partial updates)
class AccountInUpdate(BaseSchemaModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    phone: str | None = None
    full_name: str | None = None


# Schema for user login credentials
class AccountInLogin(BaseSchemaModel):
    # Both username and email are required to authenticate
    username: str
    email: pydantic.EmailStr
    password: str


# Schema representing an authenticated account with its JWT token
# Returned after successful login or registration
class AccountWithToken(BaseSchemaModel):
    # JWT access token for authenticating subsequent API requests
    token: str
    username: str
    email: pydantic.EmailStr
    # User role (e.g., "user" or "admin")
    role: str
    phone: str | None = None
    full_name: str | None = None
    # Whether the user's email has been verified
    is_verified: bool
    # Whether the account is currently active (not deactivated)
    is_active: bool
    # Whether the user is currently logged in
    is_logged_in: bool
    # Whether the user's phone number has been verified via OTP
    is_phone_verified: bool = False
    # Timestamp when the account was created
    created_at: datetime.datetime
    # Timestamp of the last account update (None if never updated)
    updated_at: datetime.datetime | None


# Wrapper response schema that includes the account ID alongside the authenticated account data
class AccountInResponse(BaseSchemaModel):
    id: int
    # Nested account object containing token and profile details
    authorized_account: AccountWithToken


# Schema for viewing a user's own profile (no token included)
class AccountProfile(BaseSchemaModel):
    id: int
    username: str
    email: pydantic.EmailStr
    role: str
    phone: str | None = None
    full_name: str | None = None
    is_verified: bool
    is_active: bool
    is_phone_verified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


# Schema for partial profile updates by the user themselves
class AccountProfileUpdate(BaseSchemaModel):
    username: str | None = None
    email: pydantic.EmailStr | None = None
    phone: str | None = None
    full_name: str | None = None


# Schema for admins to view detailed account information including block status
class AdminAccountView(BaseSchemaModel):
    id: int
    username: str
    email: pydantic.EmailStr
    role: str
    phone: str | None = None
    full_name: str | None = None
    is_verified: bool
    is_active: bool
    is_phone_verified: bool
    # Whether the account has been blocked by an admin
    is_blocked: bool
    # Reason provided by the admin when blocking the account
    blocked_reason: str | None = None
    # Timestamp of the user's most recent login
    last_login_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


# Schema for the admin action of blocking a user, with an optional reason
class AdminBlockUser(BaseSchemaModel):
    reason: str | None = None


# Paginated response schema for listing users in the admin panel
class AdminUserListResponse(BaseSchemaModel):
    # List of user accounts for the current page
    users: list[AdminAccountView]
    # Total number of matching users across all pages
    total: int
    # Current page number
    page: int
    # Number of users per page
    page_size: int
