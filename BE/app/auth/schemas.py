from typing import Literal
from pydantic import model_validator
from sqlmodel import SQLModel, Field

class Token(SQLModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"

class AccessTokenData(SQLModel):
    user_id: int
    token_type: Literal["access"]

class RefreshTokenData(SQLModel):
    user_id: int | None = None
    token_type: Literal["refresh"] | None = None

class ChangePasswordRequest(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    new_password_confirm: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("New password and confirmation do not match.")
        return self
