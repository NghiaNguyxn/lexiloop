from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep, CurrentUserDep
from app.common.responses import BaseResponse, create_success_response
from app.database.databases import SessionDep
from app.users import service as user_service
from app.users.dependencies import ActiveUserDep, UserDep
from app.users.schemas import UserAdminUpdate, UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=BaseResponse[UserResponse],
    summary="Get the current user's profile",
)
def get_my_profile(current_user: CurrentUserDep) -> BaseResponse[UserResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="User profile retrieved successfully.",
        result=current_user,
    )


@router.patch(
    "/me",
    response_model=BaseResponse[UserResponse],
    summary="Update the current user's profile",
)
def update_my_profile(
    session: SessionDep,
    current_user: CurrentUserDep,
    user_update: UserUpdate,
) -> BaseResponse[UserResponse]:
    user = user_service.update_user_profile(
        session=session,
        user_id=current_user.id,
        user_update=user_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User profile updated successfully.",
        result=user,
    )


@router.delete(
    "/me",
    response_model=BaseResponse[None],
    summary="Delete the current user's account",
)
def delete_my_account(
    session: SessionDep,
    current_user: CurrentUserDep,
) -> BaseResponse[None]:
    user_service.delete_user(session=session, user_id=current_user.id)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User account deleted successfully.",
    )


@router.get(
    "",
    response_model=BaseResponse[list[UserResponse]],
    summary="List users (admin only)",
)
def get_users(
    session: SessionDep,
    _: AdminUserDep,
    include_deleted: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> BaseResponse[list[UserResponse]]:
    users = user_service.get_users(
        session=session,
        is_deleted=None if include_deleted else False,
        skip=skip,
        limit=limit,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="Users retrieved successfully.",
        result=users,
    )


@router.get(
    "/{user_id}",
    response_model=BaseResponse[UserResponse],
    summary="Get a user by ID (admin only)",
)
def get_user(
    _: AdminUserDep,
    user: UserDep,
) -> BaseResponse[UserResponse]:
    return create_success_response(
        code=status.HTTP_200_OK,
        message="User retrieved successfully.",
        result=user,
    )


@router.patch(
    "/{user_id}",
    response_model=BaseResponse[UserResponse],
    summary="Update a user as an administrator",
)
def admin_update_user(
    user_update: UserAdminUpdate,
    _: AdminUserDep,
    user: UserDep,
    session: SessionDep,
) -> BaseResponse[UserResponse]:
    updated_user = user_service.admin_update_user(
        session=session,
        user_id=user.id,
        user_update=user_update,
    )

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User updated successfully.",
        result=updated_user,
    )


@router.delete(
    "/{user_id}",
    response_model=BaseResponse[None],
    summary="Delete a user as an administrator",
)
def admin_delete_user(
    _: AdminUserDep,
    user: ActiveUserDep,
    session: SessionDep,
) -> BaseResponse[None]:
    user_service.delete_user(session=session, user_id=user.id)

    return create_success_response(
        code=status.HTTP_200_OK,
        message="User deleted successfully.",
    )
