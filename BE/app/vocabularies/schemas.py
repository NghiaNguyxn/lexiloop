from __future__ import annotations

from datetime import datetime
import unicodedata
from sqlmodel import SQLModel
from pydantic import Field, field_validator, model_validator

from app.vocabularies.enums import CEFRLevel, PartOfSpeech


class VocabularyCreate(SQLModel):
    word: str = Field(min_length=1, max_length=100)
    items: list[VocabularyItemCreate] = Field(min_length=1)

    @field_validator("word", mode="before")
    @classmethod
    def clean_word(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        value = unicodedata.normalize("NFKC", value)
        return " ".join(value.split())


class VocabularyUpdate(SQLModel):
    word: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("word", mode="before")
    @classmethod
    def clean_word(cls, value: object) -> object:
        if value is None:
            raise ValueError("Word cannot be None for update.")

        if not isinstance(value, str):
            return value

        cleaned = unicodedata.normalize("NFKC", value)
        cleaned = " ".join(cleaned.split())

        if not cleaned:
            raise ValueError("word cannot be blank.")

        return cleaned

    @model_validator(mode="after")
    def at_least_one_field_provided(self) -> "VocabularyUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        return self


class VocabularyListResponse(SQLModel):
    id: int
    deck_id: int
    word: str
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VocabularyDetailResponse(SQLModel):
    id: int
    deck_id: int
    word: str
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[VocabularyItemResponse] = Field(default_factory=list)


class VocabularyItemCreate(SQLModel):
    part_of_speech: PartOfSpeech
    ipa: str | None = Field(default=None, max_length=200)
    english_meaning: str = Field(min_length=1, max_length=1000)
    vietnamese_meaning: str = Field(min_length=1, max_length=1000)
    grammar_note: str | None = Field(default=None, max_length=2000)
    note: str | None = Field(default=None, max_length=2000)
    topic: str | None = Field(default=None, max_length=100)
    level: CEFRLevel | None = Field(default=None)

    @field_validator("ipa", "grammar_note", "note", "topic", mode="before")
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None

    @field_validator("english_meaning", "vietnamese_meaning", mode="before")
    @classmethod
    def clean_required_meanings(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        value = value.strip()

        if not value:
            raise ValueError("Meanings cannot be blank.")

        return " ".join(value.split())


class VocabularyItemUpdate(SQLModel):
    part_of_speech: PartOfSpeech | None = None
    ipa: str | None = Field(default=None, max_length=200)
    english_meaning: str | None = Field(default=None, min_length=1, max_length=1000)
    vietnamese_meaning: str | None = Field(default=None, min_length=1, max_length=1000)
    grammar_note: str | None = Field(default=None, max_length=2000)
    note: str | None = Field(default=None, max_length=2000)
    topic: str | None = Field(default=None, max_length=100)
    level: CEFRLevel | None = None

    @field_validator("ipa", "grammar_note", "note", "topic", mode="before")
    @classmethod
    def clean_optional_text(cls, value: object,) -> object:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        cleaned = value.strip()

        return cleaned or None

    @field_validator("part_of_speech", mode="before")
    @classmethod
    def validate_part_of_speech(cls, value: object) -> object:
        if value is None:
            raise ValueError("Part of speech cannot be None for update.")
        return value

    @field_validator("english_meaning", "vietnamese_meaning", mode="before")
    @classmethod
    def clean_required_meanings(cls, value: object) -> object:
        if value is None:
            raise ValueError("Meanings cannot be None for update.")

        if not isinstance(value, str):
            return value

        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Meanings cannot be blank.")

        return " ".join(cleaned.split())

    @model_validator(mode="after")
    def at_least_one_field_provided(self) -> "VocabularyItemUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update.")

        return self


class VocabularyItemResponse(SQLModel):
    id: int
    vocabulary_id: int
    part_of_speech: PartOfSpeech
    ipa: str | None
    english_meaning: str
    vietnamese_meaning: str
    grammar_note: str | None
    note: str | None
    topic: str | None
    level: CEFRLevel | None
    position: int
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
