"""Authentication routes: OTP, Google OAuth, refresh, logout, profile."""

from fastapi import APIRouter, Cookie, Depends, Request, Response
from starlette import status

from app.api.deps import get_auth_service
from app.core.auth import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    GoogleAuthRequest,
    GoogleAuthResponse,
    LogoutResponse,
    MeUpdateRequest,
    OTPSendRequest,
    OTPSendResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    RefreshResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"
_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 3600  # 30 days


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="strict",
        path=_REFRESH_COOKIE_PATH,
        max_age=_REFRESH_COOKIE_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=_REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="strict",
        path=_REFRESH_COOKIE_PATH,
    )


@router.post("/otp/send", response_model=OTPSendResponse)
async def send_otp(
    data: OTPSendRequest,
    service: AuthService = Depends(get_auth_service),
) -> OTPSendResponse:
    return await service.send_otp(data)


@router.post("/otp/verify", response_model=OTPVerifyResponse)
async def verify_otp(
    data: OTPVerifyRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> OTPVerifyResponse:
    result, refresh_token, _jti = await service.verify_otp(
        data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, refresh_token)
    return result


@router.post("/google", response_model=GoogleAuthResponse)
async def google_login(
    data: GoogleAuthRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> GoogleAuthResponse:
    result, refresh_token, _jti = await service.google_login(
        data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    _set_refresh_cookie(response, refresh_token)
    return result


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None, alias=_REFRESH_COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
) -> RefreshResponse:
    if not refresh_token:
        from starlette.exceptions import HTTPException

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    result, new_refresh, _jti = await service.refresh_access_token(refresh_token)
    _set_refresh_cookie(response, new_refresh)
    return result


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    await service.logout(user.id)
    _clear_refresh_cookie(response)
    return LogoutResponse()


@router.get("/me", response_model=AuthUserResponse)
async def get_me(user: User = Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse.model_validate(user)


@router.patch("/me", response_model=AuthUserResponse)
async def update_me(
    data: MeUpdateRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> AuthUserResponse:
    updates = data.model_dump(exclude_unset=True)
    if updates:
        from app.repositories.user import UserRepository

        repo = UserRepository(service.session)
        user = await repo.update(user, updates)
    return AuthUserResponse.model_validate(user)
