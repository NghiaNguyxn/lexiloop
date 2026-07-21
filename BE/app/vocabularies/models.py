from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, Index, func, text
from sqlmodel import Field, SQLModel

from app.vocabularies.enums import CEFRLevel, PartOfSpeech


class Vocabulary(SQLModel, table=True):
    __tablename__ = "vocabularies"

    __table_args__ = (
        Index(
            "uq_vocabularies_deck_id_normalized_word_active",
            "deck_id",
            "normalized_word",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_vocabularies_deck_id_is_deleted_created_at",
            "deck_id",
            "is_deleted",
            "created_at",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    deck_id: int = Field(
        foreign_key="decks.id",
        ondelete="RESTRICT",
        nullable=False,
    )

    word: str = Field(nullable=False, max_length=100)

    normalized_word: str = Field(nullable=False, max_length=200)

    is_deleted: bool = Field(default=False, nullable=False)

    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )


class VocabularyItem(SQLModel, table=True):
    __tablename__ = "vocabulary_items"

    __table_args__ = (
        CheckConstraint(
            "position >= 1",
            name="ck_vocab_items_position_positive",
        ),
        Index(
            "uq_vocab_items_vocabulary_id_position_active",
            "vocabulary_id",
            "position",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_vocab_items_vocabulary_id_deleted_position",
            "vocabulary_id",
            "is_deleted",
            "position",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    vocabulary_id: int = Field(
        foreign_key="vocabularies.id",
        ondelete="RESTRICT",
        nullable=False,
    )

    part_of_speech: PartOfSpeech = Field(
        sa_type=SAEnum(
            PartOfSpeech,
            name="part_of_speech",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        nullable=False,
    )

    ipa: str | None = Field(default=None, max_length=200)

    english_meaning: str = Field(nullable=False, max_length=1000)

    vietnamese_meaning: str = Field(nullable=False, max_length=1000)

    grammar_note: str | None = Field(default=None, max_length=2000)

    note: str | None = Field(default=None, max_length=2000)

    topic: str | None = Field(default=None, max_length=100)

    level: CEFRLevel | None = Field(
        default=None,
        sa_type=SAEnum(
            CEFRLevel,
            name="cefr_level",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
    )

    position: int = Field(nullable=False)

    is_deleted: bool = Field(default=False, nullable=False)

    deleted_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
        },
    )

    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )
