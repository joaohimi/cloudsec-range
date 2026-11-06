from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    display_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=15, max_length=128)
    role_codes: list[str] = Field(default_factory=lambda: ["learner"], min_length=1, max_length=2)

    model_config = ConfigDict(extra="forbid")


class UserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=160)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")

    model_config = ConfigDict(extra="forbid")


class UserRolesUpdateRequest(BaseModel):
    role_codes: list[str] = Field(min_length=1, max_length=2)

    model_config = ConfigDict(extra="forbid")


class ManagedUserRead(BaseModel):
    id: UUID
    email: str
    display_name: str
    status: str
    roles: list[str]
    created_at: datetime
    last_login_at: datetime | None


class ManagedUserList(BaseModel):
    items: list[ManagedUserRead]
    total: int
    limit: int
    offset: int


class RoleRead(BaseModel):
    code: str
    name: str
    description: str | None
