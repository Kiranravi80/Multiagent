"""
Global Error Handler Middleware.

Maps domain exceptions to HTTP status codes.
Ensures consistent error responses across all endpoints.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    DatabaseError,
    DomainValidationError,
    DuplicateEntityError,
    EntityNotFoundError,
    PAIOSException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": exc.message, "code": exc.code, "details": exc.details},
        )

    @app.exception_handler(DuplicateEntityError)
    async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": exc.message, "code": exc.code, "details": exc.details},
        )

    @app.exception_handler(DomainValidationError)
    async def validation_handler(request: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"success": False, "error": exc.message, "code": exc.code, "details": exc.details},
        )

    @app.exception_handler(BusinessRuleViolationError)
    async def business_rule_handler(request: Request, exc: BusinessRuleViolationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": exc.message, "code": exc.code, "details": exc.details},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": exc.message, "code": exc.code},
        )

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": exc.message, "code": exc.code},
        )

    @app.exception_handler(DatabaseError)
    async def db_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        logger.error("database_error", error=exc.message, details=exc.details)
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Service temporarily unavailable", "code": exc.code},
        )

    @app.exception_handler(PAIOSException)
    async def paios_handler(request: Request, exc: PAIOSException) -> JSONResponse:
        logger.error("paios_error", error=exc.message, code=exc.code)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": exc.message, "code": exc.code},
        )

    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_error", error=str(exc), type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error", "code": "INTERNAL_ERROR"},
        )
