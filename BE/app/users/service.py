import logging
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.auth.refresh_token_service import revoke_all_refresh_tokens_for_user
from app.users.enums import Role
from app.users.models import User
from app.users.exceptions import UserAlreadyExistsError
from app.users.schemas import UserAdminUpdate, UserCreate, UserUpdate
from app.auth.security import hash_password
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_user_by_id(session: Session, user_id: int) -> User | None:
    """Retrieve a user by ID, including soft-deleted users."""

    return session.get(User, user_id)

def get_user_by_username(session: Session, username: str) -> User | None:
    """Retrieve a user by username, including soft-deleted users."""

    statement = select(User).where(User.username == username)
    return session.exec(statement).first()

def get_active_user_by_id(session: Session, user_id: int) -> User | None:
    """Retrieve an active (not deleted) user by their ID."""

    logger.info(f"Fetching active user with ID: {user_id}")
    statement = select(User).where(User.id == user_id, User.is_deleted == False)
    return session.exec(statement).first()

def get_active_user_by_username(session: Session, username: str) -> User | None:
    """Retrieve an active (not deleted) user by their username."""

    logger.info(f"Fetching active user with username: {username}")
    statement = select(User).where(User.username == username, User.is_deleted == False)
    return session.exec(statement).first()

def get_active_user_by_email(session: Session, email: str) -> User | None:
    """Retrieve an active (not deleted) user by their email."""

    logger.info(f"Fetching active user with email: {email}")
    statement = select(User).where(User.email == email, User.is_deleted == False)
    return session.exec(statement).first()

def get_active_user_by_username_or_email(session: Session, username_or_email: str) -> User | None:
    """Retrieve an active (not deleted) user by their username or email."""

    logger.info(f"Fetching active user with username or email: {username_or_email}")
    statement = select(User).where(
        User.username == username_or_email, User.is_deleted == False
    ).union(
        select(User).where(
            User.email == username_or_email, User.is_deleted == False
        )
    )
    return session.exec(statement).first()

def get_active_user_by_phone(session: Session, phone: str) -> User | None:
    """Retrieve an active (not deleted) user by their phone number."""

    logger.info(f"Fetching active user with phone: {phone}")
    statement = select(User).where(User.phone == phone, User.is_deleted == False)
    return session.exec(statement).first()

def get_users(session: Session, is_deleted: bool | None = None, skip: int = 0, limit: int = 100) -> list[User]:
    """Retrieve a list of users with pagination."""

    logger.info(f"Fetching users with skip={skip} and limit={limit}")
    statement = select(User).offset(skip).limit(limit)
    if is_deleted is not None:
        statement = statement.where(User.is_deleted == is_deleted)
    return session.exec(statement).all()

def create_user(session: Session, user_create: UserCreate) -> User:
    """Create a new user in the database."""

    logger.info(f"Creating a new user with username: {user_create.username}")

    if get_active_user_by_username(session, user_create.username):
        logger.error(f"User creation failed: Username {user_create.username} already exists.")
        raise UserAlreadyExistsError()

    if get_active_user_by_email(session, user_create.email):
        logger.error(f"User creation failed: Email {user_create.email} already exists.")
        raise UserAlreadyExistsError()

    if user_create.phone and get_active_user_by_phone(session, user_create.phone):
        logger.error(f"User creation failed: Phone {user_create.phone} already exists.")
        raise UserAlreadyExistsError()

    hashed_password = hash_password(user_create.password)
    user = User.model_validate(
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

def update_user_profile(session: Session, user_id: int, user_update: UserUpdate) -> User | None:
    """Update an existing user's information."""

    logger.info(f"Updating user with ID: {user_id}")
    user = get_active_user_by_id(session, user_id)
    if not user:
        logger.error(f"User update failed: User with ID {user_id} not found.")
        return None

    if user_update.username and user_update.username != user.username and get_active_user_by_username(session, user_update.username.strip().lower()):
        logger.error(f"User update failed: Username {user_update.username} already exists.")
        raise UserAlreadyExistsError()

    if user_update.email and user_update.email != user.email and get_active_user_by_email(session, user_update.email.strip().lower()):
        logger.error(f"User update failed: Email {user_update.email} already exists.")
        raise UserAlreadyExistsError()

    if user_update.phone and user_update.phone != user.phone and get_active_user_by_phone(session, user_update.phone.strip().lower()):
        logger.error(f"User update failed: Phone {user_update.phone} already exists.")
        raise UserAlreadyExistsError()

    update_data = user_update.model_dump(
        mode="json",
        exclude_unset=True,
    )
    user.sqlmodel_update(update_data)

    session.add(user)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing updated user to the database: {e}")
        session.rollback()
        raise UserAlreadyExistsError() from e

    session.refresh(user)
    return user

def update_avatar(session: Session, user_id: int, avatar_url: str) -> User | None:
    """Update a user's avatar URL."""

    logger.info(f"Updating avatar for user with ID: {user_id}")
    user = get_active_user_by_id(session, user_id)
    if not user:
        logger.error(f"Avatar update failed: User with ID {user_id} not found.")
        return None

    user.avatar_url = avatar_url
    session.add(user)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing avatar update to the database: {e}")
        session.rollback()
        raise UserAlreadyExistsError() from e

    session.refresh(user)
    return user

def admin_update_user(session: Session, user_id: int, user_update: UserAdminUpdate) -> User | None:
    """Update a user's information as an administrator."""

    logger.info(f"Updating user with ID: {user_id}")
    user = get_user_by_id(session, user_id)
    if not user:
        logger.error(f"User update failed: User with ID {user_id} not found.")
        return None

    should_revoke_refresh_tokens = (
        user_update.is_deleted is True and not user.is_deleted
    )
    user.sqlmodel_update(user_update.model_dump(exclude_unset=True))
    if should_revoke_refresh_tokens:
        revoke_all_refresh_tokens_for_user(session, user.id)

    session.add(user)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing updated user to the database: {e}")
        session.rollback()
        raise UserAlreadyExistsError() from e

    session.refresh(user)
    return user

def delete_user(session: Session, user_id: int) -> bool:
    """Soft delete a user by marking them as deleted."""

    logger.info(f"Deleting user with ID: {user_id}")
    user = get_active_user_by_id(session, user_id)
    if not user:
        logger.error(f"User deletion failed: User with ID {user_id} not found.")
        return False

    user.is_deleted = True
    revoke_all_refresh_tokens_for_user(session, user_id)
    session.add(user)

    try:
        session.commit()
    except IntegrityError as e:
        logger.error(f"Error committing user deletion to the database: {e}")
        session.rollback()
        raise UserAlreadyExistsError() from e

    session.refresh(user)
    return True

def create_initial_data(session: Session):
    """Initialize the database with initial data if necessary."""

    logger.info("Initializing initial data...")
    admin = get_user_by_username(session, settings.FIRST_ADMIN_USERNAME)
    if admin is not None:
        logger.info("Default admin account already exists. Skipping creation.")
        return

    logger.info("Creating default admin user.")
    admin = User(
        username=settings.FIRST_ADMIN_USERNAME,
        email=settings.FIRST_ADMIN_EMAIL,
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        role=Role.ADMIN
    )
    session.add(admin)
    try:
        session.commit()
    except Exception:
        session.rollback()
        logger.error("Failed to create default admin user.")
        raise
