from datetime import datetime

from sqlmodel import SQLModel, Field, DateTime, func, Index, text


class Collocation(SQLModel, table=True):
    __tablename__ = "collocations"

    __table_args__ = (
        Index(
            "uq_collocations_vocabulary_item_id_normalized_phrase_active",
            "vocabulary_item_id",
            "normalized_phrase",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_collocations_vocabulary_item_id_is_deleted_position",
            "vocabulary_item_id",
            "is_deleted",
            "position",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    vocabulary_item_id: int = Field(
        foreign_key="vocabulary_items.id",
        ondelete="RESTRICT",
        nullable=False,
    )

    phrase: str = Field(nullable=False, max_length=200)

    normalized_phrase: str = Field(nullable=False, max_length=200)

    english_meaning: str | None = Field(default=None, max_length=1000)

    vietnamese_meaning: str | None = Field(default=None, max_length=1000)

    note: str | None = Field(default=None, max_length=500)

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


class ExampleSentence(SQLModel, table=True):
    __tablename__ = "example_sentences"

    __table_args__ = (
        Index(
            "uq_examples_item_normalized_sentence_active",
            "vocabulary_item_id",
            "normalized_sentence",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_example_sentences_vocabulary_item_id_is_deleted_position",
            "vocabulary_item_id",
            "is_deleted",
            "position",
        ),
        Index(
            "ix_example_sentences_collocation_id_is_deleted_position",
            "collocation_id",
            "is_deleted",
            "position",
        )
    )

    id: int | None = Field(default=None, primary_key=True)

    vocabulary_item_id: int = Field(
        foreign_key="vocabulary_items.id",
        ondelete="RESTRICT",
        nullable=False,
    )

    collocation_id: int | None = Field(
        foreign_key="collocations.id",
        default=None,
    )

    sentence: str = Field(nullable=False, max_length=500)

    normalized_sentence: str = Field(nullable=False, max_length=500)

    vietnamese_meaning: str | None = Field(default=None, max_length=1000)

    note: str | None = Field(default=None, max_length=500)

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
