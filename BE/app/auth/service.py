import logging
from fastapi import Request
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, get_refresh_token_expiration, hash_refresh_token
from app.auth.models import RefreshToken
from app.auth.refresh_token_service import revoke_all_refresh_tokens_for_user,revoke_refresh_token
from app.auth.exceptions import ExpiredRefreshTokenError, InvalidCredentialsError, InvalidCurrentPasswordError, InvalidRefreshTokenError, MissingRefreshTokenError, PasswordSameAsOldError, RefreshTokenReuseError
from app.auth.schemas import ChangePasswordRequest
from app.common.time import utc_now
from app.common.exception import InternalServerError
from app.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.users.schemas import UserCreate
from app.users.service import get_active_user_by_id, get_active_user_by_username_or_email
from app.users.models import User

logger = logging.getLogger(__name__)


def register_user(session: Session, user_create: UserCreate) -> User:
    """Register a new user."""

    logger.info(f"Registering a new user with username: {user_create.username}")
    hashed_password: str = hash_password(user_create.password)

    user: User = User.model_validate(
        user_create.model_dump(mode="json", exclude={"password", "password_confirm"}),
        update={"hashed_password": hashed_password}
    )

    session.add(user)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing new user to the database: {e}")
        session.rollback()
        raise UserAlreadyExistsError() from e
    session.refresh(user)

    return user


def authenticate_user(session: Session, username_or_email: str, password: str) -> User:
    """Authenticate a user by their username or email and password."""

    logger.info(f"Attempting to log in user with username or email: {username_or_email}")

    user = get_active_user_by_username_or_email(session, username_or_email.strip().lower())
    if user is None:
        logger.warning(f"Login failed: User with username or email {username_or_email} not found.")
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect password for user {username_or_email}.")
        raise InvalidCredentialsError()

    return user


def login_user(session: Session, username_or_email: str, password: str, user_agent: str, ip_address: str) -> tuple[str, str]:
    """Authenticate the user and return access and refresh tokens."""

    user = authenticate_user(session, username_or_email, password)
    if user is None:
        logger.warning(f"Login failed: Authentication failed for user {username_or_email}.")
        raise InvalidCredentialsError()

    # Generate tokens
    access_token = create_access_token(user_id=user.id)
    raw_refresh_token = create_refresh_token()

    logger.info(f"User {username_or_email} logged in successfully from IP {ip_address} with User-Agent {user_agent}.")

    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=get_refresh_token_expiration(),
        user_agent=user_agent,
        ip_address=ip_address
    )

    session.add(refresh_token_record)
    session.commit()

    return access_token, raw_refresh_token


def rotate_refresh_token(session: Session, raw_refresh_token: str, user_agent: str, ip_address: str) -> tuple[str, str]:
    """Rotate the refresh token and return new access and refresh tokens."""

    if(not raw_refresh_token):
        logger.error("Refresh token rotation failed: No refresh token provided.")
        raise MissingRefreshTokenError()

    statement = select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_refresh_token))

    refresh_token_record = session.exec(statement).first()

    if refresh_token_record is None:
        logger.warning("Refresh token rotation failed: Invalid refresh token provided.")
        raise InvalidRefreshTokenError()

    if refresh_token_record.expires_at < utc_now():
        logger.warning(f"Refresh token rotation failed: Refresh token for user {refresh_token_record.user_id} has expired.")
        raise ExpiredRefreshTokenError()

    if refresh_token_record.revoked_at is not None:
        if refresh_token_record.replaced_by_token_id is not None:
            logger.warning(f"Refresh token rotation failed: Refresh token for user {refresh_token_record.user_id} has been revoked and replaced.")
            revoke_all_refresh_tokens_for_user(session, refresh_token_record.user_id)
            session.commit()
            raise RefreshTokenReuseError()
        logger.warning(f"Refresh token rotation failed: Refresh token for user {refresh_token_record.user_id} has been revoked.")
        revoke_all_refresh_tokens_for_user(session, refresh_token_record.user_id)
        session.commit()
        raise InvalidRefreshTokenError()


    user = get_active_user_by_id(session, refresh_token_record.user_id)
    if user is None:
        logger.error(f"Refresh token rotation failed: User with ID {refresh_token_record.user_id} not found.")
        revoke_refresh_token(refresh_token_record)
        session.commit()
        raise InvalidRefreshTokenError()

    new_refresh_token = create_refresh_token()
    new_refresh_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=get_refresh_token_expiration(),
        user_agent=user_agent,
        ip_address=ip_address
    )

    session.add(new_refresh_token_record)
    session.flush()

    revoke_refresh_token(refresh_token_record, new_refresh_token_record.id)

    session.commit()

    return create_access_token(user_id=user.id), new_refresh_token


def logout_user(session: Session, raw_refresh_token: str | None = None) -> None:
    """Log out the user by revoking the refresh token."""

    if raw_refresh_token is None:
        return

    statement = select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_refresh_token))
    refresh_token_record = session.exec(statement).first()

    if refresh_token_record is None:
        logger.warning("Invalid refresh token provided.")
        return

    if refresh_token_record.revoked_at is not None:
        return

    revoke_refresh_token(refresh_token_record)
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Error committing refresh token revocation to the database: {e}")
        session.rollback()
        raise InternalServerError("An error occurred while logging out the user.") from e


def change_password(session: Session, user_id: int, request: ChangePasswordRequest) -> User | None:
    """Update a user's password."""

    logger.info(f"Updating password for user with ID: {user_id}")

    user = get_active_user_by_id(session, user_id)
    if not user:
        logger.error(f"Password update failed: User with ID {user_id} not found.")
        raise UserNotFoundError()

    if not verify_password(request.current_password, user.hashed_password):
        logger.error(f"Password update failed: Incorrect current password for user {user_id}.")
        raise InvalidCurrentPasswordError()

    if request.new_password == request.current_password:
        logger.error("Password update failed: New password cannot be the same as the current password.")
        raise PasswordSameAsOldError()

    hashed_new_password = hash_password(request.new_password)
    user.hashed_password = hashed_new_password

    session.add(user)

    revoke_all_refresh_tokens_for_user(session, user_id)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing password change to the database for user {user_id}: {e}")
        session.rollback()
        raise InternalServerError("An error occurred while changing the password.") from e
    session.refresh(user)

    return user

def get_client_ip(request: Request) -> str:
    """Extract the client's IP address from the request headers."""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host

    return ip


def get_user_agent(request: Request) -> str:
    """Extract the User-Agent from the request headers."""
    return request.headers.get("User-Agent", "Unknown")
