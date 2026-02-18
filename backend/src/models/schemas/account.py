import datetime

import pydantic

from src.models.schemas.base import BaseSchemaModel


class AccountInCreate(BaseSchemaModel):
    username: str
    email: pydantic.EmailStr
    password: str
    phone: str | None = None
    full_name: str | None = None
    email_otp_code: str | None = None


class AccountInUpdate(BaseSchemaModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    phone: str | None = None
    full_name: str | None = None


class AccountInLogin(BaseSchemaModel):
    username: str
    email: pydantic.EmailStr
    password: str


class AccountWithToken(BaseSchemaModel):
    token: str
    username: str
    email: pydantic.EmailStr
    role: str
    phone: str | None = None
    full_name: str | None = None
    is_verified: bool
    is_active: bool
    is_logged_in: bool
    is_phone_verified: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


class AccountInResponse(BaseSchemaModel):
    id: int
    authorized_account: AccountWithToken


# New schemas for user profile
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


class AccountProfileUpdate(BaseSchemaModel):
    username: str | None = None
    email: pydantic.EmailStr | None = None
    phone: str | None = None
    full_name: str | None = None


# Admin schemas
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
    is_blocked: bool
    blocked_reason: str | None = None
    last_login_at: datetime.datetime | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime | None


class AdminBlockUser(BaseSchemaModel):
    reason: str | None = None


class AdminUserListResponse(BaseSchemaModel):
    users: list[AdminAccountView]
    total: int
    page: int
    page_size: int
