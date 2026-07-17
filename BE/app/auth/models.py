from datetime import datetime
from sqlmodel import DateTime, SQLModel, Field, func, Index

class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    __table_args__ = (
        Index("idx_refresh_tokens_user_id_expires_at", "user_id", "expires_at"),
        Index("idx_refresh_tokens_user_id_revoked_at", "user_id", "revoked_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    token_hash: str = Field(nullable=False, unique=True, max_length=128)
    expires_at: datetime = Field(
        nullable=False,
        index=True,
        sa_type=DateTime(timezone=True)
    )
    revoked_at: datetime | None = Field(
        default=None,
        index=True,
        sa_type=DateTime(timezone=True)
    )
    replaced_by_token_id: int | None = Field(default=None, foreign_key="refresh_tokens.id", index=True)
    user_agent: str | None = Field(default=None, max_length=500)
    ip_address: str | None = Field(default=None, max_length=100)
    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now()
        }
    )
    last_used_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
