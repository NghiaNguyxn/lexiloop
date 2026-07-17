from datetime import datetime
import unicodedata
from sqlmodel import SQLModel
from pydantic import Field, field_validator, model_validator


class DeckCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)

    description: str | None = Field(default=None, max_length=1000)

    is_public: bool = Field(default=False)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        value = unicodedata.normalize("NFKC", value)
        return " ".join(value.split())

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value

        value = value.strip()
        return value or None


class DeckUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)

    description: str | None = Field(default=None, max_length=1000)

    is_public: bool | None = Field(default=None)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        value = unicodedata.normalize("NFKC", value)

        return " ".join(value.split()).strip()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value

        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def at_least_one_field_provided(self) -> "DeckUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        for field_name in ["name", "is_public"]:
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be set to None.")

        return self


class DeckResponse(SQLModel):
    id: int
    user_id: int
    name: str
    description: str | None
    is_public: bool
    created_at: datetime
    updated_at: datetime


class DeckAdminResponse(DeckResponse):
    is_deleted: bool
    deleted_at: datetime | None
