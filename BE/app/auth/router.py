from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.exceptions import MissingRefreshTokenError
from app.database.databases import SessionDep
from app.common.responses import BaseResponse, create_success_response
from app.users.schemas import UserCreate, UserResponse
from app.auth.schemas import ChangePasswordRequest, Token
from app.auth import service as auth_service
from app.core.config import settings
from app.auth.jwt import get_refresh_cookie_max_age
from app.auth.dependencies import CurrentUserDep


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(
    session: SessionDep,
    user_create: UserCreate
) -> BaseResponse[UserResponse]:
    return create_success_response(
        status.HTTP_201_CREATED,
        message="User registered successfully.",
        result=auth_service.register_user(
            session=session,
            user_create=user_create
        )
    )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user and return access and refresh tokens",
)
def login_user(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response
) -> Token:
    access_token, refresh_token = auth_service.login_user(
        username_or_email=form_data.username,
        password=form_data.password,
        session=session,
        user_agent=auth_service.get_user_agent(request),
        ip_address=auth_service.get_client_ip(request)
    )

    set_refresh_token_cookie(response, refresh_token)

    return Token(access_token=access_token)


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Refresh the access token using the refresh token",
)
def refresh_access_token(
    session: SessionDep,
    request: Request,
    response: Response
) -> Token:
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise MissingRefreshTokenError()

    access_token, new_refresh_token = auth_service.rotate_refresh_token(
        session=session,
        raw_refresh_token=refresh_token,
        user_agent=auth_service.get_user_agent(request),
        ip_address=auth_service.get_client_ip(request)
    )

    set_refresh_token_cookie(response, new_refresh_token)

    return Token(access_token=access_token)

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout the user and revoke the refresh token",
)
def logout_user(
    session: SessionDep,
    request: Request,
    response: Response
) -> BaseResponse[None]:
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)

    auth_service.logout_user(session=session, raw_refresh_token=refresh_token)

    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/auth"
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User logged out successfully.",
        result=None
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change the password for the current user",
)
def change_password(
    session: SessionDep,
    current_user: CurrentUserDep,
    response: Response,
    password_change_request: ChangePasswordRequest
) -> BaseResponse[None]:
    auth_service.change_password(
        session=session,
        user_id=current_user.id,
        request=password_change_request
    )

    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/auth"
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Password changed successfully.",
        result=None
    )


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token in an HTTP-only cookie."""
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=get_refresh_cookie_max_age(),
        path="/auth",
    )
