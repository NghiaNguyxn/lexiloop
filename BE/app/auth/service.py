import logging
import secrets
import re
from fastapi import Request
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.security import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, get_refresh_token_expiration, hash_refresh_token
from app.auth.models import RefreshToken, UserIdentity
from app.auth.refresh_token_service import revoke_all_refresh_tokens_for_user,revoke_refresh_token
from app.auth.enums import IdentityProvider
from app.auth.google_verifier import verify_google_credential
from app.auth.exceptions import (
    ExpiredRefreshTokenError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    InvalidRefreshTokenError,
    MissingRefreshTokenError,
    PasswordSameAsOldError,
    RefreshTokenReuseError,
    PasswordNotConfiguredError,
    PasswordAlreadyConfiguredError,
    AccountUnavailableError,
    GoogleLinkRequiredError,
    GoogleAlreadyLinkedError,
    GoogleIdentityAlreadyLinkedError,
    GoogleUnlinkNotAllowedError,
)
from app.auth.schemas import (
    AuthMethodsResponse,
    ChangePasswordRequest,
    GoogleIdentityData,
    SetPasswordRequest,
)
from app.common.time import utc_now
from app.common.exception import InternalServerError
from app.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.users.schemas import UserCreate
from app.users.enums import Role
from app.users.service import (
    get_active_user_by_id,
    get_active_user_by_username_or_email,
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
)
from app.users.models import User

logger = logging.getLogger(__name__)


_GOOGLE_NONCE_BYTES = 32  # Number of bytes for the Google nonce
_GOOGLE_USERNAME_MAX_LENGTH = 50  # Maximum length for a Google username
_GOOGLE_USERNAME_MAX_ATTEMPTS = 10  # Maximum attempts to generate a unique Google username
_GOOGLE_USERNAME_SUFFIX_BYTES = 3 # Number of bytes for the random suffix in Google username generation
_INVALID_GOOGLE_USERNAME_CHARS = re.compile(r"[^a-zA-Z0-9_.-]")  # Regex to match invalid characters in Google usernames


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

    normalized_identifier = username_or_email.strip().lower()

    user = get_active_user_by_username_or_email(session, normalized_identifier)
    if user is None or user.hashed_password is None:
        logger.warning("Password authentication failed.")
        raise InvalidCredentialsError()

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Login failed: Incorrect password for user {username_or_email}.")
        raise InvalidCredentialsError()

    return user


def issue_auth_session(
    session: Session,
    user: User,
    user_agent: str,
    ip_address: str
) -> tuple[str, str]:
    """
    Create a LexiLoop access token and refresh token for the authenticated user.

    This function intentionally does not commit the transaction.
    """

    user_id = user.id

    if user_id is None:
        logger.error("User ID is None. Cannot issue auth session.")
        raise InternalServerError(message="Cannot issue a session for an unpersisted user.")

    access_token = create_access_token(user_id=user_id)
    raw_refresh_token = create_refresh_token()

    refresh_token_record = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_refresh_token),
        expires_at=get_refresh_token_expiration(),
        user_agent=user_agent,
        ip_address=ip_address
    )

    session.add(refresh_token_record)

    return access_token, raw_refresh_token


def login_user(session: Session, username_or_email: str, password: str, user_agent: str, ip_address: str) -> tuple[str, str]:
    """Authenticate the user and return access and refresh tokens."""

    user = authenticate_user(
        session=session,
        username_or_email=username_or_email,
        password=password
    )

    access_token, raw_refresh_token = issue_auth_session(
        session=session,
        user=user,
        user_agent=user_agent,
        ip_address=ip_address
    )

    logger.info(f"User {username_or_email} logged in successfully from IP {ip_address} with User-Agent {user_agent}.")

    try:
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error committing auth session to the database for user {username_or_email}: {e}")
        session.rollback()
        raise InternalServerError("An error occurred while creating the auth session.") from e

    return access_token, raw_refresh_token


def login_with_google(
    session: Session,
    credential: str,
    nonce: str,
    user_agent: str,
    ip_address: str
) -> tuple[str, str]:
    """Authenticate with Google and issue a LexiLoop session."""

    identity_data: GoogleIdentityData = verify_google_credential(
        credential=credential,
        expected_nonce=nonce
    )

    try:
        identity: UserIdentity | None = get_identity_by_provider_subject(
            session=session,
            provider=IdentityProvider.GOOGLE,
            provider_subject=identity_data.subject
        )

        if identity is not None:
            user = get_user_by_id(
                session=session,
                user_id=identity.user_id
            )

            if user is None or user.is_deleted:
                logger.warning(f"Google login failed: User with ID {identity.user_id} not found or is deleted.")
                raise AccountUnavailableError()

            touch_google_identity(
                session=session,
                identity=identity,
                identity_data=identity_data,
            )

        else:
            email = str(identity_data.email).lower()

            existing_user = get_user_by_email(
                session,
                email,
            )

            if existing_user is not None:
                if existing_user.is_deleted:
                    logger.warning(f"Google login failed: account is unavailable.")
                    raise AccountUnavailableError()

                raise GoogleLinkRequiredError()

            username = generate_unique_google_username(
                session=session,
                email=email,
            )

            full_name = None
            if identity_data.full_name:
                full_name = " ".join(identity_data.full_name.strip().split())[:100]

            avatar_url = None
            if identity_data.avatar_url:
                candidate_avatar_url = str(identity_data.avatar_url).strip()

                if len(candidate_avatar_url) <= 2048:
                    avatar_url = candidate_avatar_url

            user = User(
                username=username,
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                hashed_password=None,
                role=Role.USER,
            )

            session.add(user)
            session.flush()

            user_id = user.id

            if user_id is None:
                logger.error("Unable to create the Google user. User ID is None after flush.")
                raise InternalServerError(message="Unable to create the Google user.")

            create_google_identity(
                session=session,
                user_id=user_id,
                identity_data=identity_data
            )

        access_token, raw_refresh_token = issue_auth_session(
            session=session,
            user=user,
            user_agent=user_agent,
            ip_address=ip_address
        )

        session.commit()

        return access_token, raw_refresh_token

    except SQLAlchemyError as e:
        logger.exception("Database error during Google sign-in.")
        session.rollback()
        raise InternalServerError("An error occurred during the Google login process.") from e


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


def set_password(
    session: Session,
    user_id: int,
    request: SetPasswordRequest,
) -> User:
    """Set the initial password for an account that does not have one."""

    logger.info("Setting the initial password for user ID %s.", user_id)

    statement = (
        select(User)
        .where(
            User.id == user_id,
            User.is_deleted.is_(False),
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    user = session.exec(statement).first()

    if user is None:
        logger.warning(
            "Initial password setup failed: user ID %s was not found.",
            user_id,
        )
        raise UserNotFoundError()

    if user.hashed_password is not None:
        logger.warning(
            "Initial password setup failed: user ID %s already has a password.",
            user_id,
        )
        raise PasswordAlreadyConfiguredError()

    user.hashed_password = hash_password(request.new_password)
    session.add(user)

    revoke_all_refresh_tokens_for_user(
        session=session,
        user_id=user_id,
    )

    try:
        session.commit()
    except SQLAlchemyError as error:
        logger.exception(
            "Database error while setting the initial password for user ID %s.",
            user_id,
        )
        session.rollback()
        raise InternalServerError(
            "An error occurred while setting the password."
        ) from error

    session.refresh(user)

    return user


def change_password(session: Session, user_id: int, request: ChangePasswordRequest) -> User | None:
    """Update a user's password."""

    logger.info(f"Updating password for user with ID: {user_id}")

    user = get_active_user_by_id(session, user_id)
    if not user:
        logger.error(f"Password update failed: User with ID {user_id} not found.")
        raise UserNotFoundError()

    if user.hashed_password is None:
        logger.error(f"Password update failed: User with ID {user_id} does not have a password set.")
        raise PasswordNotConfiguredError()

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


def generate_google_nonce() -> str:
    """Generate a secure random nonce for Google OAuth2 authentication."""

    return secrets.token_urlsafe(_GOOGLE_NONCE_BYTES)


def get_identity_by_provider_subject(
    session: Session,
    provider: IdentityProvider,
    provider_subject: str
) -> UserIdentity | None:
    """Retrieve an external identity by provider and provider subject."""

    statement = select(UserIdentity).where(
        UserIdentity.provider == provider,
        UserIdentity.provider_subject == provider_subject
    )

    return session.exec(statement).first()


def get_identity_by_user_and_provider(
    session: Session,
    user_id: int,
    provider: IdentityProvider
) -> UserIdentity | None:
    """Retrieve a provider identity linked to a LexiLoop user."""

    statement = select(UserIdentity).where(
        UserIdentity.user_id == user_id,
        UserIdentity.provider == provider
    )

    return session.exec(statement).first()


def create_google_identity(
    session: Session,
    user_id: int,
    identity_data: GoogleIdentityData
) -> UserIdentity:
    """Create a Google identity without committing the transaction."""

    identity = UserIdentity(
        user_id=user_id,
        provider=IdentityProvider.GOOGLE,
        provider_subject=identity_data.subject,
        provider_email=str(identity_data.email),
        last_used_at=utc_now()
    )

    session.add(identity)

    return identity


def touch_google_identity(
    session: Session,
    identity: UserIdentity,
    identity_data: GoogleIdentityData
) -> None:
    """Update Google identity metadata after successful verification."""

    identity.provider_email = str(identity_data.email)
    identity.last_used_at = utc_now()

    session.add(identity)


def get_auth_methods(
    session: Session,
    user: User
) -> AuthMethodsResponse:
    """Retrieve the authentication methods available for a user."""

    user_id = user.id

    if user_id is None:
        logger.error("User ID is None. Cannot retrieve auth methods.")
        raise InternalServerError(message="Cannot retrieve auth methods for an unpersisted user.")

    google_identity = get_identity_by_user_and_provider(
        session=session,
        user_id=user_id,
        provider=IdentityProvider.GOOGLE
    )

    return AuthMethodsResponse(
        password=user.hashed_password is not None,
        google=google_identity is not None
    )


def generate_unique_google_username(
    session: Session,
    email: str,
) -> str:
    """Generate a unique username based on the Google email address."""

    local_part = email.partition("@")[0].strip().lower()

    base = _INVALID_GOOGLE_USERNAME_CHARS.sub("", local_part).strip("_.-")

    if not base:
        base = "user"

    if len(base) < 3:
        base = f"{base}-user"

    base = base[:_GOOGLE_USERNAME_MAX_LENGTH].rstrip("_.-")

    if get_user_by_username(session, base) is None:
        return base

    for _ in range(_GOOGLE_USERNAME_MAX_ATTEMPTS):
        suffix = secrets.token_hex(_GOOGLE_USERNAME_SUFFIX_BYTES)
        max_prefix_length = (_GOOGLE_USERNAME_MAX_LENGTH - len(suffix) - 1)

        prefix = base[:max_prefix_length].rstrip("_.-")
        candidate = f"{prefix}-{suffix}"

        if get_user_by_username(session, candidate) is None:
            return candidate

    raise InternalServerError("Unable to generate a unique username after multiple attempts.")


def link_google_identity(
    session: Session,
    user: User,
    credential: str,
    nonce: str
) -> None:
    """Link a verified Google identity to an existing user."""

    user_id = user.id

    if user_id is None:
        logger.error("User ID is None. Cannot link Google identity.")
        raise InternalServerError(message="Cannot link Google identity to an unpersisted user.")

    identity_data: GoogleIdentityData = verify_google_credential(
        credential=credential,
        expected_nonce=nonce
    )

    try:
        identity = get_identity_by_provider_subject(
            session=session,
            provider=IdentityProvider.GOOGLE,
            provider_subject=identity_data.subject
        )

        if identity is not None:
            if identity.user_id != user_id:
                logger.warning(f"Google identity linking failed: Identity already linked to another user (ID: {identity.user_id}).")
                raise GoogleIdentityAlreadyLinkedError()

            touch_google_identity(
                session=session,
                identity=identity,
                identity_data=identity_data
            )

            session.commit()
            return

        current_google_identity = get_identity_by_user_and_provider(
            session=session,
            user_id=user_id,
            provider=IdentityProvider.GOOGLE
        )

        if current_google_identity is not None:
            logger.warning(f"Google identity linking failed: User {user_id} already has a linked Google identity.")
            raise GoogleAlreadyLinkedError()

        create_google_identity(
            session=session,
            user_id=user_id,
            identity_data=identity_data
        )

        session.commit()

    except SQLAlchemyError as e:
        logger.exception("Database error during Google identity linking.")
        session.rollback()
        raise InternalServerError("An error occurred while linking the Google identity.") from e


def unlink_google_identity(
    session: Session,
    user: User
) -> None:
    """Remove Google as a sign-in method."""

    user_id = user.id

    if user_id is None:
        logger.error("User ID is None. Cannot unlink Google identity.")
        raise InternalServerError(message="Cannot unlink Google identity from an unpersisted user.")

    if user.hashed_password is None:
        raise GoogleUnlinkNotAllowedError()

    try:
        identity = get_identity_by_user_and_provider(
                session=session,
                user_id=user_id,
                provider=IdentityProvider.GOOGLE
            )

        if identity is None:
            return

        session.delete(identity)
        session.commit()

    except SQLAlchemyError as e:
        logger.exception("Database error during Google identity unlinking.")
        session.rollback()
        raise InternalServerError("An error occurred while unlinking the Google identity.") from e
