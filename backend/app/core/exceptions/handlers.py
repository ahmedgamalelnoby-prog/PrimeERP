from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions.base import AppException


logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    errors = list(exc.errors)

    if not errors:
        errors.append(
            {
                "code": exc.error_code,
                "message": exc.message,
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "errors": errors,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors: list[dict[str, Any]] = []

    for error in exc.errors():
        location = error.get(
            "loc",
            (),
        )

        field = ".".join(
            str(item)
            for item in location
            if item not in {
                "body",
                "query",
                "path",
            }
        )

        errors.append(
            {
                "field": field or None,
                "code": error.get("type"),
                "message": error.get(
                    "msg",
                    "Invalid value.",
                ),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed.",
            "errors": errors,
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    logger.exception(
        "Database integrity error",
        exc_info=exc,
    )

    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": "The operation conflicts with existing data.",
            "errors": [
                {
                    "code": "database_integrity_error",
                    "message": (
                        "A duplicate or invalid related record "
                        "prevented the operation."
                    ),
                }
            ],
        },
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception(
        "Database error",
        exc_info=exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "A database error occurred.",
            "errors": [
                {
                    "code": "database_error",
                    "message": "The database operation failed.",
                }
            ],
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled application error",
        exc_info=exc,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred.",
            "errors": [
                {
                    "code": "internal_server_error",
                    "message": (
                        "The server could not complete the request."
                    ),
                }
            ],
        },
    )


def register_exception_handlers(
    app: FastAPI,
) -> None:
    app.add_exception_handler(
        AppException,
        app_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        IntegrityError,
        integrity_error_handler,
    )

    app.add_exception_handler(
        SQLAlchemyError,
        sqlalchemy_error_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )