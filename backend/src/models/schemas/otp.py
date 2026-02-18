import pydantic

from src.models.schemas.base import BaseSchemaModel


class OTPSendRequest(BaseSchemaModel):
    """Request to send OTP"""
    phone: str | None = None
    email: pydantic.EmailStr | None = None
    purpose: str = "login"  # login, verify_phone, verify_email, reset_password

    @pydantic.validator("phone", "email")
    def at_least_one_required(cls, v, values):
        if not v and not values.get("phone") and not values.get("email"):
            raise ValueError("Either phone or email must be provided")
        return v


class OTPVerifyRequest(BaseSchemaModel):
    """Request to verify OTP"""
    phone: str | None = None
    email: pydantic.EmailStr | None = None
    code: str
    purpose: str = "login"


class OTPSendResponse(BaseSchemaModel):
    """Response after sending OTP"""
    message: str
    expires_in_seconds: int = 600  # 10 minutes


class OTPLoginRequest(BaseSchemaModel):
    """Login using OTP"""
    phone: str | None = None
    email: pydantic.EmailStr | None = None
    code: str


class PasswordResetRequest(BaseSchemaModel):
    """Request password reset"""
    email: pydantic.EmailStr


class PasswordResetConfirm(BaseSchemaModel):
    """Confirm password reset with OTP"""
    email: pydantic.EmailStr
    code: str
    new_password: str


class EmailOTPSendRequest(BaseSchemaModel):
    """Request to send OTP to email for login/signup"""
    email: pydantic.EmailStr


class EmailOTPVerifyRequest(BaseSchemaModel):
    """Request to verify email OTP for login/signup"""
    email: pydantic.EmailStr
    code: str
