from datetime import datetime

from sqlalchemy import DateTime, Index, func, text
from sqlmodel import Field, SQLModel


class Deck(SQLModel, table=True):
    __tablename__ = "decks"

    __table_args__ = (
        Index(
            "uq_decks_user_id_normalized_name_active",
            "user_id",
            "normalized_name",
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
        Index(
            "ix_decks_user_id_is_deleted_created_at",
            "user_id",
            "is_deleted",
            "created_at",
        ),
        Index(
            "ix_decks_is_public_is_deleted_created_at",
            "is_public",
            "is_deleted",
            "created_at",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="users.id", nullable=False)

    name: str = Field(nullable=False, max_length=100)

    normalized_name: str = Field(nullable=False, max_length=100)

    description: str | None = Field(default=None, max_length=1000)

    is_public: bool = Field(default=False, nullable=False)

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
