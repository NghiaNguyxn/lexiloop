from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.exceptions import (
    InvalidGoogleNonceError,
    MissingRefreshTokenError,
)
from app.database.databases import SessionDep
from app.common.responses import BaseResponse, create_success_response
from app.users.schemas import UserCreate, UserResponse
from app.auth.schemas import (
    AuthMethodsResponse,
    ChangePasswordRequest,
    GoogleCredentialRequest,
    GoogleNonceResponse,
    SetPasswordRequest,
    Token,
)
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
    "/google",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user using Google OAuth and return access and refresh tokens",
)
def login_with_google(
    session: SessionDep,
    request: Request,
    response: Response,
    google_request: GoogleCredentialRequest
) -> Token:

    nonce = get_google_nonce_from_cookie(request)

    access_token, raw_refresh_token = auth_service.login_with_google(
        session=session,
        credential=google_request.credential,
        nonce=nonce,
        user_agent=auth_service.get_user_agent(request),
        ip_address=auth_service.get_client_ip(request)
    )

    set_refresh_token_cookie(
        response=response,
        refresh_token=raw_refresh_token)

    delete_google_nonce_cookie(response)

    response.headers["Cache-Control"] = "no-store, max-age=0"

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

    delete_refresh_token_cookie(response)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User logged out successfully.",
        result=None
    )


@router.post(
    "/set-password",
    status_code=status.HTTP_200_OK,
    summary="Set the initial password for the current user",
)
def set_password(
    session: SessionDep,
    current_user: CurrentUserDep,
    response: Response,
    password_request: SetPasswordRequest,
) -> BaseResponse[None]:
    auth_service.set_password(
        session=session,
        user_id=current_user.id,
        request=password_request,
    )

    delete_refresh_token_cookie(response)
    response.headers["Cache-Control"] = "no-store, max-age=0"

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Password set successfully.",
        result=None,
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

    delete_refresh_token_cookie(response)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Password changed successfully.",
        result=None
    )


@router.get(
    "/google/nonce",
    status_code=status.HTTP_200_OK,
    summary="Generate a nonce for Google authentication",
)
def generate_google_nonce(response: Response) -> BaseResponse[GoogleNonceResponse]:
    nonce = auth_service.generate_google_nonce()

    set_google_nonce_cookie(
        response=response,
        nonce=nonce
    )

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Google nonce generated successfully.",
        result=GoogleNonceResponse(nonce=nonce)
    )


@router.post(
    "/google/link",
    status_code=status.HTTP_200_OK,
    summary="Link a Google account to the current user",
)
def link_google_account(
    session: SessionDep,
    current_user: CurrentUserDep,
    request: Request,
    response: Response,
    google_request: GoogleCredentialRequest
) -> BaseResponse[None]:
    nonce = get_google_nonce_from_cookie(request)

    auth_service.link_google_identity(
        session=session,
        user=current_user,
        credential=google_request.credential,
        nonce=nonce,
    )

    delete_google_nonce_cookie(response)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Google account linked successfully.",
        result=None
    )


@router.delete(
    "/google/link",
    status_code=status.HTTP_200_OK,
    summary="Unlink the Google account from the current user",
)
def unlink_google_account(
    session: SessionDep,
    current_user: CurrentUserDep
) -> BaseResponse[None]:
    auth_service.unlink_google_identity(
        session=session,
        user=current_user
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Google account unlinked successfully.",
        result=None
    )

@router.get(
    "/methods",
    status_code=status.HTTP_200_OK,
    summary="Get the available authentication methods for the current user",
)
def get_auth_methods(
    session: SessionDep,
    current_user: CurrentUserDep,
    response: Response
) -> BaseResponse[AuthMethodsResponse]:
    auth_methods = auth_service.get_auth_methods(
        session=session,
        user=current_user
    )

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Authentication methods retrieved successfully.",
        result=auth_methods
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


def delete_refresh_token_cookie(response: Response) -> None:
    """Delete the refresh-token cookie using the same scope used to set it."""

    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/auth",
    )


def set_google_nonce_cookie(response: Response, nonce: str) -> None:
    """Set the Google nonce in an HTTP-only cookie."""

    response.set_cookie(
        key=settings.GOOGLE_NONCE_COOKIE_NAME,
        value=nonce,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        max_age=settings.GOOGLE_NONCE_EXPIRE_SECONDS,
        path="/auth/google",
    )


def get_google_nonce_from_cookie(request: Request) -> str:
    """Retrieve the Google nonce from the its HttpOnly cookie."""

    nonce = request.cookies.get(settings.GOOGLE_NONCE_COOKIE_NAME)
    if not nonce:
        raise InvalidGoogleNonceError()

    return nonce


def delete_google_nonce_cookie(response: Response) -> None:
    """Delete the Google nonce cookie after an authentication attempt."""

    response.delete_cookie(
        key=settings.GOOGLE_NONCE_COOKIE_NAME,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/auth/google",
    )
