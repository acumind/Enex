"""Authentication service: OTP send/verify, Google OAuth, token refresh, logout."""

import logging
import re
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import get_settings
from app.core.rate_limit import otp_send_limiter, otp_verify_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_otp,
    is_refresh_token_valid,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    store_refresh_token,
    verify_otp_hash,
    verify_token,
)
from app.integrations.email.resend_adapter import ResendAdapter
from app.integrations.oauth.google_verifier import GoogleUserInfo, GoogleVerifier
from app.integrations.sms.msg91_adapter import MSG91Adapter
from app.models.login_event import LoginEvent
from app.models.user import OTPCode, User
from app.repositories.otp import OTPRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AuthUserResponse,
    GoogleAuthRequest,
    GoogleAuthResponse,
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    RefreshResponse,
)

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.otp_repo = OTPRepository(session)
        self.email_adapter = ResendAdapter()
        self.sms_adapter = MSG91Adapter()
        self.google_verifier = GoogleVerifier()

    def _is_email(self, identifier: str) -> bool:
        return bool(_EMAIL_RE.match(identifier))

    # ------------------------------------------------------------------
    # OTP Send
    # ------------------------------------------------------------------

    async def send_otp(self, data: OTPSendRequest) -> OTPSendResponse:
        settings = get_settings()

        # Rate limit
        await otp_send_limiter.check(data.identifier)

        # Cooldown: check if there's a recent unexpired OTP
        latest = await self.otp_repo.get_latest_unused(data.identifier, data.purpose)
        if latest:
            now = datetime.now(UTC).replace(tzinfo=None)
            elapsed = (now - latest.created_at).total_seconds()
            if elapsed < settings.OTP_COOLDOWN_SECONDS:
                remaining = int(settings.OTP_COOLDOWN_SECONDS - elapsed)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {remaining} seconds before requesting a new code",
                )

        # Generate and hash OTP
        plain_otp = generate_otp(settings.OTP_LENGTH)
        hashed = hash_otp(plain_otp)

        # Invalidate old OTPs for this identifier/purpose
        await self.otp_repo.invalidate_all(data.identifier, data.purpose)

        # Store new OTP
        otp_record = OTPCode(
            id=uuid.uuid4(),
            identifier=data.identifier,
            code=hashed,
            purpose=data.purpose,
            expires_at=(datetime.now(UTC) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)).replace(tzinfo=None),
        )
        await self.otp_repo.create(otp_record)

        # Deliver via email or SMS
        if self._is_email(data.identifier):
            sent = await self.email_adapter.send_otp(data.identifier, plain_otp)
        else:
            sent = await self.sms_adapter.send_otp(data.identifier, plain_otp)

        if not sent:
            logger.warning("OTP delivery failed for %s (provider returned False)", data.identifier)

        return OTPSendResponse(
            message="Verification code sent",
            identifier=data.identifier,
            expires_in_seconds=settings.OTP_EXPIRE_MINUTES * 60,
        )

    # ------------------------------------------------------------------
    # OTP Verify
    # ------------------------------------------------------------------

    async def _record_login(
        self,
        user_id: uuid.UUID,
        method: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        event = LoginEvent(
            user_id=user_id,
            login_method=method,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        self.session.add(event)
        await self.session.flush()

    async def verify_otp(
        self,
        data: OTPVerifyRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[OTPVerifyResponse, str, str]:
        """Verify OTP and return (response, refresh_token, jti)."""
        settings = get_settings()

        # Rate limit
        await otp_verify_limiter.check(data.identifier)

        # Lookup latest unused OTP
        otp_record = await self.otp_repo.get_latest_unused(data.identifier, data.purpose)
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid OTP found. Please request a new code.",
            )

        # Check max attempts
        if otp_record.attempts >= settings.OTP_MAX_ATTEMPTS:
            await self.otp_repo.mark_used(otp_record.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many incorrect attempts. Please request a new code.",
            )

        # Increment attempts before verification
        await self.otp_repo.increment_attempts(otp_record.id)

        # Constant-time verify
        if not verify_otp_hash(data.code, otp_record.code):
            remaining = settings.OTP_MAX_ATTEMPTS - (otp_record.attempts + 1)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid code. {remaining} attempt(s) remaining.",
            )

        # Mark OTP as used
        await self.otp_repo.mark_used(otp_record.id)

        # Get or create user
        user = await self._get_or_create_user_from_otp(data.identifier, data.purpose)

        # Issue tokens
        access_token = create_access_token(user.id, user.role)
        refresh_token, jti = create_refresh_token(user.id, user.role)
        await store_refresh_token(user.id, jti)

        # Update last login
        await self.user_repo.update(user, {"last_login_at": func.now()})

        # Record login event
        await self._record_login(user.id, "otp", ip_address, user_agent)

        user_response = AuthUserResponse.model_validate(user)
        return (
            OTPVerifyResponse(access_token=access_token, user=user_response),
            refresh_token,
            jti,
        )

    # ------------------------------------------------------------------
    # Google Login
    # ------------------------------------------------------------------

    async def google_login(
        self,
        data: GoogleAuthRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[GoogleAuthResponse, str, str]:
        """Verify Google token and return (response, refresh_token, jti)."""
        # Try id_token first, fallback to access_token
        google_user = None
        if data.id_token:
            google_user = await self.google_verifier.verify_id_token(data.id_token)
        if not google_user and data.access_token:
            google_user = await self.google_verifier.verify_access_token(data.access_token)

        if not google_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token",
            )

        # Get or create user (link by email)
        user = await self._get_or_create_user_from_oauth(google_user)

        # Issue tokens
        access_token = create_access_token(user.id, user.role)
        refresh_token, jti = create_refresh_token(user.id, user.role)
        await store_refresh_token(user.id, jti)

        # Update last login
        await self.user_repo.update(user, {"last_login_at": func.now()})

        # Record login event
        await self._record_login(user.id, "google", ip_address, user_agent)

        user_response = AuthUserResponse.model_validate(user)
        return (
            GoogleAuthResponse(access_token=access_token, user=user_response),
            refresh_token,
            jti,
        )

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def refresh_access_token(self, token_str: str) -> tuple[RefreshResponse, str, str]:
        """Rotate refresh token. Returns (response, new_refresh_token, new_jti)."""
        from jose import JWTError

        try:
            token_data = verify_token(token_str)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            ) from None

        if token_data.token_type != "refresh" or not token_data.jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        # Check Redis allowlist (fail-closed)
        if not await is_refresh_token_valid(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        # Verify user is still active
        user = await self.user_repo.get_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        # Rotate: revoke old, issue new
        await revoke_refresh_token(token_data.jti)
        new_access = create_access_token(user.id, user.role)
        new_refresh, new_jti = create_refresh_token(user.id, user.role)
        await store_refresh_token(user.id, new_jti)

        return RefreshResponse(access_token=new_access), new_refresh, new_jti

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    async def logout(self, user_id: uuid.UUID) -> None:
        await revoke_all_refresh_tokens(user_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_or_create_user_from_otp(self, identifier: str, purpose: str) -> User:
        """Find existing user by identifier or create a new one. Updates verification flags."""
        is_email = self._is_email(identifier)

        if is_email:
            user = await self.user_repo.get_by_email(identifier)
        else:
            user = await self.user_repo.get_by_phone(identifier)

        if user:
            # Update verification status and auth methods
            updates: dict = {}
            if is_email and not user.is_email_verified:
                updates["is_email_verified"] = True
            elif not is_email and not user.is_phone_verified:
                updates["is_phone_verified"] = True

            method = "email" if is_email else "phone"
            if method not in (user.auth_methods or []):
                updates["auth_methods"] = list(user.auth_methods or []) + [method]

            if updates:
                await self.user_repo.update(user, updates)
            return user

        # Create new user
        user = User(
            id=uuid.uuid4(),
            email=identifier if is_email else None,
            phone=identifier if not is_email else None,
            is_email_verified=is_email,
            is_phone_verified=not is_email,
            auth_methods=["email" if is_email else "phone"],
        )
        await self.user_repo.create(user)
        return user

    async def _get_or_create_user_from_oauth(self, google_user: GoogleUserInfo) -> User:
        """Find user by email (account linking) or create new. Updates OAuth fields."""
        user = await self.user_repo.get_by_email(google_user.email)

        if user:
            # Link Google OAuth info and update fields
            updates: dict = {
                "oauth_provider": "google",
                "oauth_id": google_user.google_id,
                "is_email_verified": True,
            }
            if google_user.name and not user.name:
                updates["name"] = google_user.name
            if google_user.picture and not user.avatar_url:
                updates["avatar_url"] = google_user.picture

            if "google" not in (user.auth_methods or []):
                updates["auth_methods"] = list(user.auth_methods or []) + ["google"]

            await self.user_repo.update(user, updates)
            return user

        # Create new user from Google
        user = User(
            id=uuid.uuid4(),
            email=google_user.email,
            name=google_user.name,
            avatar_url=google_user.picture,
            is_email_verified=True,
            oauth_provider="google",
            oauth_id=google_user.google_id,
            auth_methods=["google"],
        )
        await self.user_repo.create(user)
        return user
