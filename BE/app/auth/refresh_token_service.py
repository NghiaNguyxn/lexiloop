import logging

from sqlmodel import Session, select

from app.auth.models import RefreshToken
from app.common.time import utc_now


logger = logging.getLogger(__name__)


def revoke_refresh_token(refresh_token_record: RefreshToken, new_refresh_token_id: int | None = None,) -> None:
    """Mark one refresh token as revoked without committing the session."""

    logger.info(
        "Revoking refresh token for user %s.",
        refresh_token_record.user_id,
    )
    now = utc_now()
    refresh_token_record.revoked_at = now
    refresh_token_record.last_used_at = now
    refresh_token_record.replaced_by_token_id = new_refresh_token_id


def revoke_all_refresh_tokens_for_user(session: Session, user_id: int,) -> None:
    """Mark all active refresh tokens for a user as revoked without committing."""

    logger.info("Revoking all refresh tokens for user %s.", user_id)
    statement = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked_at.is_(None),
    )
    active_tokens = session.exec(statement).all()
    now = utc_now()

    for token in active_tokens:
        token.revoked_at = now
        token.last_used_at = now
        token.replaced_by_token_id = None
