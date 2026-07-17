import logging
from typing import Optional, Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.common.exception as exception
from app.common.responses import BaseResponse

logger = logging.getLogger("app")

def register_exception_handlers(app: FastAPI):
    """Register all custom exception handlers to the FastAPI app."""

    def create_error_response(
        code: int,
        message: str,
        error_code: Optional[str] = None,
        errors: Optional[list[Any]] = None,
        headers: dict = None
    ) -> JSONResponse:
        """Create response for error"""

        response_data = BaseResponse(
            code=code,
            message=message,
            result=None,
            error_code=error_code,
            errors=errors
        )

        return JSONResponse(
            status_code=code,
            content=response_data.model_dump(),
            headers=headers
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        error_code = (
            "UNAUTHORIZED"
            if exc.status_code == status.HTTP_401_UNAUTHORIZED
            else "HTTP_ERROR"
        )

        return create_error_response(
            code=exc.status_code,
            message=str(exc.detail),
            error_code=error_code,
            headers=exc.headers,
        )

    @app.exception_handler(exception.AppError)
    async def app_exception_handler(request: Request, exc: exception.AppError):
        return create_error_response(
            code=exc.status_code,
            message=exc.message,
            error_code=exc.error_code,
            errors=exc.details
        )

    @app.exception_handler(exception.UnAuthorizedError)
    async def unauthorized_exception_handler(request: Request, exc: exception.UnAuthorizedError):
        return create_error_response(
            code=status.HTTP_401_UNAUTHORIZED,
            message=exc.message,
            error_code=exc.error_code,
            headers={"WWW-Authenticate": "Bearer"}
        )

    @app.exception_handler(exception.ForbiddenError)
    async def forbidden_exception_handler(request: Request, exc: exception.ForbiddenError):
        return create_error_response(
            code=status.HTTP_403_FORBIDDEN,
            message=exc.message,
            error_code=exc.error_code
        )

    @app.exception_handler(exception.NotFoundError)
    async def not_found_exception_handler(request: Request, exc: exception.NotFoundError):
        return create_error_response(
            code=status.HTTP_404_NOT_FOUND,
            message=exc.message,
            error_code=exc.error_code
        )

    @app.exception_handler(exception.ConflictError)
    async def conflict_exception_handler(request: Request, exc: exception.ConflictError):
        return create_error_response(
            code=status.HTTP_409_CONFLICT,
            message=exc.message,
            error_code=exc.error_code
        )

    @app.exception_handler(exception.ValidationError)
    async def validation_exception_handler(request: Request, exc: exception.ValidationError):
        return create_error_response(
            code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message=exc.message,
            error_code=exc.error_code,
            errors=exc.details
        )

    @app.exception_handler(exception.InternalServerError)
    async def internal_server_exception_handler(request: Request, exc: exception.InternalServerError):
        return create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=exc.message,
            error_code=exc.error_code
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled system error: {exc}", exc_info=True)

        return create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            error_code="INTERNAL_SERVER_ERROR"
        )
