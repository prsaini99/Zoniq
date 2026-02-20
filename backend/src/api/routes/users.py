# User profile routes: view/update profile, phone verification, and email verification
# All endpoints require authentication (get_current_user dependency)
import fastapi
from fastapi import Depends

from src.api.dependencies.auth import get_current_user
from src.api.dependencies.repository import get_repository
from src.models.db.account import Account
from src.models.schemas.account import AccountProfile, AccountProfileUpdate
from src.models.schemas.otp import OTPSendRequest, OTPSendResponse, OTPVerifyRequest
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.otp import OTPCRUDRepository
from src.services.otp_service import otp_service, sms_service, email_service

# All user-related routes are grouped under the /users prefix
router = fastapi.APIRouter(prefix="/users", tags=["users"])


# GET /users/me - Retrieve the authenticated user's profile information
@router.get(
    "/me",
    name="users:get-current-user",
    response_model=AccountProfile,
    status_code=fastapi.status.HTTP_200_OK,
)
async def get_current_user_profile(
    current_user: Account = Depends(get_current_user),
) -> AccountProfile:
    """Get current user's profile"""
    # Map the database Account model to the AccountProfile response schema
    return AccountProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        full_name=current_user.full_name,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        is_phone_verified=current_user.is_phone_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


# PATCH /users/me - Partially update the authenticated user's profile fields
@router.patch(
    "/me",
    name="users:update-current-user",
    response_model=AccountProfile,
    status_code=fastapi.status.HTTP_200_OK,
)
async def update_current_user_profile(
    profile_update: AccountProfileUpdate,
    current_user: Account = Depends(get_current_user),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountProfile:
    """Update current user's profile"""
    # If the username is being changed, verify the new one is not already taken
    if profile_update.username and profile_update.username != current_user.username:
        try:
            await account_repo.is_username_taken(username=profile_update.username)
        except Exception:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken",
            )

    # If the email is being changed, verify the new one is not already registered
    if profile_update.email and profile_update.email != current_user.email:
        try:
            await account_repo.is_email_taken(email=profile_update.email)
        except Exception:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )

    # Apply the partial update and return the refreshed profile
    updated_account = await account_repo.update_profile(
        account_id=current_user.id,
        profile_update=profile_update,
    )

    return AccountProfile(
        id=updated_account.id,
        username=updated_account.username,
        email=updated_account.email,
        role=updated_account.role,
        phone=updated_account.phone,
        full_name=updated_account.full_name,
        is_verified=updated_account.is_verified,
        is_active=updated_account.is_active,
        is_phone_verified=updated_account.is_phone_verified,
        created_at=updated_account.created_at,
        updated_at=updated_account.updated_at,
    )


# ==================== Phone Verification ====================
# Two-step flow: send an OTP to the user's phone, then confirm it


# POST /users/me/verify-phone - Send an OTP to the user's registered phone number
@router.post(
    "/me/verify-phone",
    name="users:send-phone-verification",
    response_model=OTPSendResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def send_phone_verification(
    current_user: Account = Depends(get_current_user),
    otp_repo: OTPCRUDRepository = Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> OTPSendResponse:
    """Send OTP to verify phone number"""
    # Guard: user must have a phone number on their profile before verification
    if not current_user.phone:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone number not set. Update your profile first.",
        )

    # Guard: skip if phone is already verified
    if current_user.is_phone_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone is already verified",
        )

    # Generate a new OTP and invalidate any prior phone-verification OTPs
    code = otp_service.generate_otp()
    expires_at = otp_service.get_expiry_time()

    await otp_repo.invalidate_previous_otps(purpose="verify_phone", phone=current_user.phone)
    await otp_repo.create_otp(
        code=code,
        purpose="verify_phone",
        expires_at=expires_at,
        user_id=current_user.id,
        phone=current_user.phone,
    )

    # Deliver the OTP via SMS
    await sms_service.send_otp(phone=current_user.phone, code=code)

    return OTPSendResponse(
        message="Verification OTP sent to your phone",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


# POST /users/me/verify-phone/confirm - Submit the OTP to complete phone verification
@router.post(
    "/me/verify-phone/confirm",
    name="users:confirm-phone-verification",
    status_code=fastapi.status.HTTP_200_OK,
)
async def confirm_phone_verification(
    request: OTPVerifyRequest,
    current_user: Account = Depends(get_current_user),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> dict:
    """Confirm phone verification with OTP"""
    # Guard: no-op if already verified
    if current_user.is_phone_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone is already verified",
        )

    # Validate the OTP against the database
    otp = await otp_repo.get_valid_otp(
        code=request.code,
        purpose="verify_phone",
        phone=current_user.phone,
    )

    if not otp:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # Consume the OTP and flag the phone as verified on the account
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    await account_repo.verify_phone(account_id=current_user.id)

    return {"message": "Phone verified successfully"}


# ==================== Email Verification ====================
# Two-step flow: send an OTP to the user's email, then confirm it


# POST /users/me/verify-email - Send an OTP to the user's registered email address
@router.post(
    "/me/verify-email",
    name="users:send-email-verification",
    response_model=OTPSendResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def send_email_verification(
    current_user: Account = Depends(get_current_user),
    otp_repo: OTPCRUDRepository = Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> OTPSendResponse:
    """Send OTP to verify email address"""
    # Guard: skip if email is already verified
    if current_user.is_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Generate a new OTP and invalidate any prior email-verification OTPs
    code = otp_service.generate_otp()
    expires_at = otp_service.get_expiry_time()

    await otp_repo.invalidate_previous_otps(purpose="verify_email", email=current_user.email)
    await otp_repo.create_otp(
        code=code,
        purpose="verify_email",
        expires_at=expires_at,
        user_id=current_user.id,
        email=current_user.email,
    )

    # Deliver the OTP via email
    await email_service.send_otp(email=current_user.email, code=code)

    return OTPSendResponse(
        message="Verification OTP sent to your email",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


# POST /users/me/verify-email/confirm - Submit the OTP to complete email verification
@router.post(
    "/me/verify-email/confirm",
    name="users:confirm-email-verification",
    status_code=fastapi.status.HTTP_200_OK,
)
async def confirm_email_verification(
    request: OTPVerifyRequest,
    current_user: Account = Depends(get_current_user),
    account_repo: AccountCRUDRepository = Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> dict:
    """Confirm email verification with OTP"""
    # Guard: no-op if already verified
    if current_user.is_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Validate the OTP against the database
    otp = await otp_repo.get_valid_otp(
        code=request.code,
        purpose="verify_email",
        email=current_user.email,
    )

    if not otp:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # Consume the OTP and flag the email as verified on the account
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    await account_repo.verify_email(account_id=current_user.id)

    return {"message": "Email verified successfully"}
