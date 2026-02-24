"""Authentication request/response schemas."""

import re
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class OTPPurpose(StrEnum):
    login = "login"
    verify_email = "verify_email"
    verify_phone = "verify_phone"


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+\d{10,14}$")


class OTPSendRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=320)
    purpose: OTPPurpose = OTPPurpose.login

    @model_validator(mode="after")
    def validate_identifier(self) -> "OTPSendRequest":
        val = self.identifier.strip()
        if not (_EMAIL_RE.match(val) or _PHONE_RE.match(val)):
            msg = "identifier must be a valid email or phone number (E.164 format)"
            raise ValueError(msg)
        self.identifier = val
        return self


class OTPSendResponse(BaseModel):
    message: str
    identifier: str
    expires_in_seconds: int


class OTPVerifyRequest(BaseModel):
    identifier: str = Field(..., min_length=5, max_length=320)
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    purpose: OTPPurpose = OTPPurpose.login


class AuthUserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    phone: str | None
    name: str | None
    avatar_url: str | None
    role: str
    is_email_verified: bool
    is_phone_verified: bool
    auth_methods: list[str]
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class OTPVerifyResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class GoogleAuthRequest(BaseModel):
    id_token: str | None = None
    access_token: str | None = None

    @model_validator(mode="after")
    def require_at_least_one_token(self) -> "GoogleAuthRequest":
        if not self.id_token and not self.access_token:
            msg = "At least one of id_token or access_token must be provided"
            raise ValueError(msg)
        return self


class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class MeUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    avatar_url: str | None = Field(None, max_length=500)
