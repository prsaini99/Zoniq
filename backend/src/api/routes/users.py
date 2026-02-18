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

router = fastapi.APIRouter(prefix="/users", tags=["users"])


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
    # Check if username is being changed and if it's taken
    if profile_update.username and profile_update.username != current_user.username:
        try:
            await account_repo.is_username_taken(username=profile_update.username)
        except Exception:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken",
            )

    # Check if email is being changed and if it's taken
    if profile_update.email and profile_update.email != current_user.email:
        try:
            await account_repo.is_email_taken(email=profile_update.email)
        except Exception:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered",
            )

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
    if not current_user.phone:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone number not set. Update your profile first.",
        )

    if current_user.is_phone_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone is already verified",
        )

    # Generate and send OTP
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

    await sms_service.send_otp(phone=current_user.phone, code=code)

    return OTPSendResponse(
        message="Verification OTP sent to your phone",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


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
    if current_user.is_phone_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Phone is already verified",
        )

    # Verify OTP
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

    # Mark OTP as used
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    # Verify phone
    await account_repo.verify_phone(account_id=current_user.id)

    return {"message": "Phone verified successfully"}


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
    if current_user.is_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Generate and send OTP
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

    await email_service.send_otp(email=current_user.email, code=code)

    return OTPSendResponse(
        message="Verification OTP sent to your email",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


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
    if current_user.is_verified:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Verify OTP
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

    # Mark OTP as used
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    # Verify email
    await account_repo.verify_email(account_id=current_user.id)

    return {"message": "Email verified successfully"}
