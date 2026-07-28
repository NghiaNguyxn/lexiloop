from __future__ import annotations

from datetime import datetime
from sqlmodel import SQLModel
from pydantic import Field, field_validator, model_validator


class CollocationCreate(SQLModel):
    phrase: str = Field(min_length=1, max_length=200)
    english_meaning: str | None = Field(default=None, max_length=1000)
    vietnamese_meaning: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("phrase", mode="before")
    @classmethod
    def clean_phrase(cls, value: object) -> object:
        if value is None:
            raise ValueError("Phrase cannot be None.")

        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Phrase cannot be blank.")

        return " ".join(cleaned.split())

    @field_validator("english_meaning", "vietnamese_meaning", "note", mode="before")
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None


class CollocationUpdate(SQLModel):
    phrase: str | None = Field(default=None, min_length=1, max_length=200)
    english_meaning: str | None = Field(default=None, max_length=1000)
    vietnamese_meaning: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("phrase", mode="before")
    @classmethod
    def clean_phrase(cls, value: object) -> object:
        if value is None:
            raise ValueError("Phrase cannot be None for update.")

        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Phrase cannot be blank.")

        return " ".join(cleaned.split())

    @field_validator("english_meaning", "vietnamese_meaning", "note", mode="before")
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None

    @model_validator(mode="after")
    def validate_at_least_one_fields(self) -> CollocationUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        return self


class CollocationResponse(SQLModel):
    id: int
    vocabulary_item_id: int
    phrase: str
    english_meaning: str | None
    vietnamese_meaning: str | None
    note: str | None
    position: int
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ExampleSentenceCreate(SQLModel):
    collocation_id: int | None = Field(default=None, ge=1)
    sentence: str = Field(min_length=1, max_length=500)
    vietnamese_meaning: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("sentence", mode="before")
    @classmethod
    def clean_sentence(cls, value: object) -> object:
        if value is None:
            raise ValueError("Sentence cannot be None.")

        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Sentence cannot be blank.")

        return " ".join(cleaned.split())

    @field_validator(
        "vietnamese_meaning", "note", mode="before"
    )
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None


class ExampleSentenceUpdate(SQLModel):
    collocation_id: int | None = Field(default=None, ge=1)
    sentence: str | None = Field(default=None, min_length=1, max_length=500)
    vietnamese_meaning: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=500)

    @field_validator("sentence", mode="before")
    @classmethod
    def clean_sentence(cls, value: object) -> object:
        if value is None:
            raise ValueError("Sentence cannot be None for update.")

        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Sentence cannot be blank.")

        return " ".join(cleaned.split())

    @field_validator(
        "vietnamese_meaning", "note", mode="before"
    )
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None

    @model_validator(mode="after")
    def validate_at_least_one_fields(self) -> ExampleSentenceUpdate:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        return self


class ExampleSentenceResponse(SQLModel):
    id: int
    vocabulary_item_id: int
    collocation_id: int | None
    sentence: str
    vietnamese_meaning: str | None
    note: str | None
    position: int
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
