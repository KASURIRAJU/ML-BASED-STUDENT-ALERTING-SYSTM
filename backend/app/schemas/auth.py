"""Authentication request/response schemas with no credential output fields."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.user import UserRole

Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]
EmailAddress = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailAddress
    password: Password


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailAddress
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailAddress
    role: UserRole
    is_active: bool
    created_at: datetime


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_identifier: str
    first_name: str
    last_name: str
    current_semester: int
    program: str


class FacultyProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_identifier: str
    first_name: str
    last_name: str
    department: str


class CurrentUserRead(UserProfileRead):
    student: StudentProfileRead | None = None
    faculty: FacultyProfileRead | None = None


class AdminUserCreate(RegisterRequest):
    role: UserRole
