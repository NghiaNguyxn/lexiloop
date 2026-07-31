from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Initial Admin Account
    FIRST_ADMIN_USERNAME: str
    FIRST_ADMIN_EMAIL: str
    FIRST_ADMIN_PASSWORD: str

    # Authentication / JWT
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    REFRESH_COOKIE_NAME: str
    REFRESH_COOKIE_SECURE: bool
    REFRESH_COOKIE_SAMESITE: str

    # Google Sign-In
    GOOGLE_CLIENT_ID: str
    GOOGLE_NONCE_COOKIE_NAME: str = "google_oauth_nonce"
    GOOGLE_NONCE_EXPIRE_SECONDS: int = 300

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # Frontend URLs
    FRONTEND_URL: str | None = None
    FRONTEND_VERIFY_PATH: str | None = None
    FRONTEND_RESET_PASSWORD_PATH: str | None = None
    CORS_ORIGINS: list[str]

    # Timezone
    APP_TIMEZONE: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / '.env',
        env_file_encoding='utf-8',
        extra='allow'
    )

settings = Settings()