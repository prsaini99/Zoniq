import logging

import fastapi
from fastapi import Request

from src.api.dependencies.repository import get_repository
from src.models.schemas.account import AccountInCreate, AccountInLogin, AccountInResponse, AccountWithToken
from src.models.schemas.otp import (
    OTPSendResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailOTPSendRequest,
    EmailOTPVerifyRequest,
)
from src.repository.crud.account import AccountCRUDRepository
from src.repository.crud.otp import OTPCRUDRepository
from src.securities.authorizations.jwt import jwt_generator
from src.services.otp_service import otp_service, email_service as mock_email_service
from src.services.email_service import email_service as smtp_email_service
from src.utilities.exceptions.database import EntityAlreadyExists
from src.utilities.exceptions.http.exc_400 import (
    http_exc_400_credentials_bad_signin_request,
    http_exc_400_credentials_bad_signup_request,
)

logger = logging.getLogger(__name__)

router = fastapi.APIRouter(prefix="/auth", tags=["authentication"])


def _build_account_response(account, access_token: str) -> AccountInResponse:
    """Helper to build account response with token"""
    return AccountInResponse(
        id=account.id,
        authorized_account=AccountWithToken(
            token=access_token,
            username=account.username,
            email=account.email,
            role=account.role,
            phone=account.phone,
            full_name=account.full_name,
            is_verified=account.is_verified,
            is_active=account.is_active,
            is_logged_in=account.is_logged_in,
            is_phone_verified=account.is_phone_verified,
            created_at=account.created_at,
            updated_at=account.updated_at,
        ),
    )


@router.post(
    "/signup",
    name="auth:signup",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_201_CREATED,
)
async def signup(
    account_create: AccountInCreate,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = fastapi.Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> AccountInResponse:
    """Register a new user account (requires email OTP verification)"""
    # Verify email OTP code
    if not account_create.email_otp_code:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Email verification code is required",
        )

    otp = await otp_repo.get_valid_otp(
        code=account_create.email_otp_code,
        purpose="email_login",
        email=account_create.email,
    )

    if not otp:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Check username separately for specific error message
    try:
        await account_repo.is_username_taken(username=account_create.username)
    except EntityAlreadyExists:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{account_create.username}' is already taken",
        )

    # Check email separately for specific error message
    try:
        await account_repo.is_email_taken(email=account_create.email)
    except EntityAlreadyExists:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{account_create.email}' is already registered",
        )

    # Mark OTP as used after all validations pass
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    new_account = await account_repo.create_account(account_create=account_create)
    access_token = jwt_generator.generate_access_token(account=new_account)

    # Send welcome email via SMTP
    try:
        await smtp_email_service.send_welcome(to_email=new_account.email, username=new_account.username)
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {new_account.email}: {e}")

    return _build_account_response(new_account, access_token)


@router.post(
    path="/signin",
    name="auth:signin",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_202_ACCEPTED,
)
async def signin(
    account_login: AccountInLogin,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
) -> AccountInResponse:
    """Sign in with username, email, and password"""
    try:
        db_account = await account_repo.read_user_by_password_authentication(account_login=account_login)

    except Exception:
        raise await http_exc_400_credentials_bad_signin_request()

    if db_account.is_blocked:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )

    # Update last login and get refreshed account
    db_account = await account_repo.update_last_login(account_id=db_account.id)

    access_token = jwt_generator.generate_access_token(account=db_account)

    return _build_account_response(db_account, access_token)


# ==================== Email OTP Authentication ====================


@router.post(
    "/email-otp/send",
    name="auth:email-otp-send",
    response_model=OTPSendResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def send_email_otp(
    request: EmailOTPSendRequest,
    otp_repo: OTPCRUDRepository = fastapi.Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> OTPSendResponse:
    """Send OTP to email address for login/signup."""
    code = otp_service.generate_otp()
    expires_at = otp_service.get_expiry_time()

    await otp_repo.invalidate_previous_otps(purpose="email_login", email=request.email)

    await otp_repo.create_otp(
        code=code,
        purpose="email_login",
        expires_at=expires_at,
        email=request.email,
    )

    email_sent = await smtp_email_service.send_otp_email(
        to_email=request.email,
        code=code,
        expires_minutes=otp_service.otp_expiry_minutes,
    )

    if not email_sent:
        logger.error(f"Failed to send OTP email to {request.email}")
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again.",
        )

    return OTPSendResponse(
        message="Verification code sent to your email",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


@router.post(
    "/email-otp/verify",
    name="auth:email-otp-verify",
    response_model=AccountInResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def verify_email_otp(
    request: EmailOTPVerifyRequest,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = fastapi.Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> AccountInResponse:
    """Verify email OTP and login or auto-register the user."""
    otp = await otp_repo.get_valid_otp(
        code=request.code,
        purpose="email_login",
        email=request.email,
    )

    if not otp:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    try:
        db_account = await account_repo.read_account_by_email(email=request.email)
    except Exception:
        db_account = None

    if db_account:
        # Existing user: login
        if db_account.is_blocked:
            raise fastapi.HTTPException(
                status_code=fastapi.status.HTTP_403_FORBIDDEN,
                detail="Account is blocked",
            )

        if not db_account.is_verified:
            await account_repo.verify_email(account_id=db_account.id)

        db_account = await account_repo.update_last_login(account_id=db_account.id)

    else:
        # New user: auto-register
        username = await account_repo.generate_unique_username(email=request.email)
        db_account = await account_repo.create_account_from_email_otp(
            email=request.email,
            username=username,
        )

        try:
            await smtp_email_service.send_welcome(to_email=db_account.email, username=db_account.username)
        except Exception as e:
            logger.warning(f"Failed to send welcome email to {db_account.email}: {e}")

    access_token = jwt_generator.generate_access_token(account=db_account)

    return _build_account_response(db_account, access_token)


# ==================== Password Reset ====================


@router.post(
    "/forgot-password",
    name="auth:forgot-password",
    response_model=OTPSendResponse,
    status_code=fastapi.status.HTTP_200_OK,
)
async def forgot_password(
    request: PasswordResetRequest,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = fastapi.Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> OTPSendResponse:
    """Request password reset OTP"""
    # Check if user exists
    try:
        account = await account_repo.read_account_by_email(email=request.email)
    except Exception:
        # Don't reveal if email exists or not
        return OTPSendResponse(
            message="If the email exists, an OTP has been sent",
            expires_in_seconds=otp_service.get_expiry_seconds(),
        )

    if not account:
        return OTPSendResponse(
            message="If the email exists, an OTP has been sent",
            expires_in_seconds=otp_service.get_expiry_seconds(),
        )

    # Generate and send OTP
    code = otp_service.generate_otp()
    expires_at = otp_service.get_expiry_time()

    await otp_repo.invalidate_previous_otps(purpose="reset_password", email=request.email)
    await otp_repo.create_otp(
        code=code,
        purpose="reset_password",
        expires_at=expires_at,
        user_id=account.id,
        email=request.email,
    )

    await mock_email_service.send_password_reset(email=request.email, code=code)

    return OTPSendResponse(
        message="If the email exists, an OTP has been sent",
        expires_in_seconds=otp_service.get_expiry_seconds(),
    )


@router.post(
    "/reset-password",
    name="auth:reset-password",
    status_code=fastapi.status.HTTP_200_OK,
)
async def reset_password(
    request: PasswordResetConfirm,
    account_repo: AccountCRUDRepository = fastapi.Depends(get_repository(repo_type=AccountCRUDRepository)),
    otp_repo: OTPCRUDRepository = fastapi.Depends(get_repository(repo_type=OTPCRUDRepository)),
) -> dict:
    """Reset password using OTP"""
    # Verify OTP
    otp = await otp_repo.get_valid_otp(
        code=request.code,
        purpose="reset_password",
        email=request.email,
    )

    if not otp:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )

    # Get user
    account = await account_repo.read_account_by_email(email=request.email)
    if not account:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Mark OTP as used
    await otp_repo.mark_otp_as_used(otp_id=otp.id)

    # Update password
    await account_repo.update_password(account_id=account.id, new_password=request.new_password)

    return {"message": "Password reset successfully"}
