from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth.exceptions import InvalidCredentialsError
from app.auth.jwt import verify_access_token
from app.common.exception import ForbiddenError
from app.database.databases import SessionDep
from app.users.enums import Role
from app.users.models import User
from app.users.service import get_active_user_by_id

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth_scheme)],
) -> User:
    token_data = verify_access_token(token)
    if token_data.user_id is None:
        raise InvalidCredentialsError()

    user = get_active_user_by_id(session=session, user_id=token_data.user_id)
    if user is None:
        raise InvalidCredentialsError()

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUserDep) -> User:
    if current_user.role != Role.ADMIN:
        raise ForbiddenError(
            message="Admin permission is required.",
            error_code="ADMIN_PERMISSION_REQUIRED",
        )

    return current_user


AdminUserDep = Annotated[User, Depends(require_admin)]
