import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=100)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class LoginIn(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class Consents(BaseModel):
    voice_transcript: bool
    analytics: bool


class ConsentsPatch(BaseModel):
    voice_transcript: bool | None = None
    analytics: bool | None = None


class ProfileOut(BaseModel):
    display_name: str
    education_level: str | None
    target_roles: list[str]


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime
    profile: ProfileOut
    consents: Consents


class ProfilePatch(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    education_level: str | None = Field(default=None, max_length=100)
    target_roles: list[str] | None = Field(default=None, max_length=10)

    @field_validator("target_roles")
    @classmethod
    def _roles(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if any(not r.strip() or len(r) > 80 for r in v):
            raise ValueError("Each role must be 1 to 80 characters.")
        return [r.strip() for r in v]


class DeleteMeIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
