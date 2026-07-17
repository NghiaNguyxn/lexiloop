from typing import Annotated

from fastapi import Depends

from app.database.databases import SessionDep
from app.users.exceptions import UserNotFoundError
from app.users.models import User
from app.users.service import get_active_user_by_id, get_user_by_id


def get_user_or_404(user_id: int, session: SessionDep) -> User:
    user = get_user_by_id(session=session, user_id=user_id)
    if user is None:
        raise UserNotFoundError()

    return user


def get_active_user_or_404(user_id: int, session: SessionDep) -> User:
    user = get_active_user_by_id(session=session, user_id=user_id)
    if user is None:
        raise UserNotFoundError()

    return user


UserDep = Annotated[User, Depends(get_user_or_404)]
ActiveUserDep = Annotated[User, Depends(get_active_user_or_404)]
