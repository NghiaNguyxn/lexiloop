from datetime import datetime

from sqlmodel import SQLModel
from pydantic import EmailStr, Field, HttpUrl, field_validator, model_validator

from app.users.enums import Role


USERNAME_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$"
PHONE_PATTERN = r"^\+[1-9][0-9]{6,13}$"


class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN)
    email: EmailStr
    phone: str | None = Field(pattern=PHONE_PATTERN, max_length=20, default=None)
    full_name: str | None = Field(min_length=1, max_length=100, default=None)
    avatar_url: HttpUrl | None = None
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str

    @field_validator("username", mode="before")
    @classmethod
    def normalized_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalized_phone(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalized_full_name(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None

        value = " ".join(value.strip().split())
        return value

    @model_validator(mode="after")
    def validate_password_identity(self) -> "UserCreate":
        password_lower = self.password.casefold()
        username_lower = self.username.casefold()
        email_lower = str(self.email).split("@")[0].casefold()

        if password_lower in (username_lower, email_lower):
            raise ValueError("Password should not be the same as username or email.")

        return self

    @model_validator(mode="after")
    def password_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match.")
        return self


class UserResponse(SQLModel):
    id: int
    username: str
    email: EmailStr
    phone: str | None
    full_name: str | None
    avatar_url: HttpUrl | None
    role: Role
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

class UserUpdate(SQLModel):
    username: str | None = Field(min_length=3, max_length=50, pattern=USERNAME_PATTERN, default=None)
    email: EmailStr | None = None
    phone: str | None = Field(pattern=PHONE_PATTERN, max_length=20, default=None)
    full_name: str | None = Field(min_length=1, max_length=100, default=None)
    avatar_url: HttpUrl | None = None

    @field_validator("username", mode="before")
    @classmethod
    def normalized_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalized_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalized_phone(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalized_full_name(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None

        value = " ".join(value.strip().split())
        return value

    @model_validator(mode="after")
    def validate_update(self) -> "UserUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        for field_name in ["username", "email"]:
            if(field_name in self.model_fields_set and getattr(self, field_name) is None):
                raise ValueError(f"{field_name} cannot be set to None.")
        return self

class UserAdminUpdate(SQLModel):
    role: Role | None = None
    is_deleted: bool | None = None

    @model_validator(mode="after")
    def validate_admin_update(self) -> "UserAdminUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for admin update.")

        for field_name in self.model_fields_set:
            if(field_name in self.model_fields_set and getattr(self, field_name) is None):
                raise ValueError(f"{field_name} cannot be set to None.")
        return self
