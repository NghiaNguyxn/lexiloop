from datetime import datetime

from sqlmodel import DateTime, Field, SQLModel, func

from app.users.enums import Role


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False, max_length=50)
    email: str = Field(unique=True, index=True, nullable=False, max_length=254)
    phone: str | None = Field(default=None, unique=True, index=True, max_length=20)
    full_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=2048)
    role: Role = Field(default=Role.USER, nullable=False)
    hashed_password: str = Field(nullable=False, max_length=255)
    is_deleted: bool = Field(default=False, nullable=False)
    reset_token: str | None = Field(default=None, max_length=255)
    reset_token_expire: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()}
    )

    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),
            "server_default": func.now()
        }
    )
