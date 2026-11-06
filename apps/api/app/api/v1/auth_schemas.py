from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: UUID
    email: str
    display_name: str
    roles: list[str]
    permissions: list[str]


class AuthResponse(BaseModel):
    user: UserRead
    csrf_token: str
    expires_at: datetime


class CurrentUserResponse(BaseModel):
    user: UserRead
    expires_at: datetime


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None
    ip_address: str | None
    user_agent: str | None
    is_current: bool


class SessionList(BaseModel):
    items: list[SessionRead]


class MessageResponse(BaseModel):
    message: str
