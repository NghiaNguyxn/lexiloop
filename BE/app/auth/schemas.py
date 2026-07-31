from typing import Literal
from pydantic import EmailStr, Field, HttpUrl, field_validator, model_validator
from sqlmodel import SQLModel

class Token(SQLModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

class AccessTokenData(SQLModel):
    user_id: int
    token_type: Literal["access"]

class ChangePasswordRequest(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("New password and confirmation do not match.")

        return self


class SetPasswordRequest(SQLModel):
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("New password and confirmation do not match.")

        return self


class GoogleCredentialRequest(SQLModel):
    credential: str = Field(min_length=1, max_length=4096)

    @field_validator("credential", mode="before")
    @classmethod
    def normalize_credential(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()

        return value


class GoogleNonceResponse(SQLModel):
    nonce: str = Field(min_length=32, max_length=128)


class AuthMethodsResponse(SQLModel):
    password: bool
    google: bool


class GoogleIdentityData(SQLModel):
    subject: str = Field(min_length=1, max_length=255)
    email: EmailStr
    full_name: str | None = None
    avatar_url: HttpUrl | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value
