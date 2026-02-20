# OTP (One-Time Password) schemas for sending, verifying OTPs and password reset flows
import pydantic

from src.models.schemas.base import BaseSchemaModel


# Schema for requesting an OTP to be sent to a phone number or email
class OTPSendRequest(BaseSchemaModel):
    """Request to send OTP"""
    # Phone number to send the OTP to (at least one of phone or email required)
    phone: str | None = None
    # Email address to send the OTP to (at least one of phone or email required)
    email: pydantic.EmailStr | None = None
    # Purpose of the OTP: login, verify_phone, verify_email, or reset_password
    purpose: str = "login"  # login, verify_phone, verify_email, reset_password

    # Validator ensuring at least one delivery method (phone or email) is provided
    @pydantic.validator("phone", "email")
    def at_least_one_required(cls, v, values):
        if not v and not values.get("phone") and not values.get("email"):
            raise ValueError("Either phone or email must be provided")
        return v


# Schema for verifying an OTP code received by the user
class OTPVerifyRequest(BaseSchemaModel):
    """Request to verify OTP"""
    phone: str | None = None
    email: pydantic.EmailStr | None = None
    # The OTP code entered by the user
    code: str
    # Must match the purpose used when sending the OTP
    purpose: str = "login"


# Response returned after successfully sending an OTP
class OTPSendResponse(BaseSchemaModel):
    """Response after sending OTP"""
    # Confirmation message (e.g., "OTP sent successfully")
    message: str
    # Number of seconds until the OTP expires (default 10 minutes)
    expires_in_seconds: int = 600  # 10 minutes


# Schema for logging in using an OTP instead of a password
class OTPLoginRequest(BaseSchemaModel):
    """Login using OTP"""
    phone: str | None = None
    email: pydantic.EmailStr | None = None
    # The OTP code to authenticate with
    code: str


# Schema for initiating a password reset by providing the user's email
class PasswordResetRequest(BaseSchemaModel):
    """Request password reset"""
    # Email address of the account to reset the password for
    email: pydantic.EmailStr


# Schema for confirming a password reset with the OTP and new password
class PasswordResetConfirm(BaseSchemaModel):
    """Confirm password reset with OTP"""
    # Email of the account being reset
    email: pydantic.EmailStr
    # OTP code received for password reset verification
    code: str
    # The new password to set for the account
    new_password: str


# Schema for requesting an email-based OTP for passwordless login or signup
class EmailOTPSendRequest(BaseSchemaModel):
    """Request to send OTP to email for login/signup"""
    email: pydantic.EmailStr


# Schema for verifying an email OTP during passwordless login or signup
class EmailOTPVerifyRequest(BaseSchemaModel):
    """Request to verify email OTP for login/signup"""
    email: pydantic.EmailStr
    # The OTP code sent to the email
    code: str
