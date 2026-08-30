from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


DataType = TypeVar("DataType")


class APIResponse(
    BaseModel,
    Generic[DataType],
):
    success: bool = True
    message: str = "Operation completed successfully."
    data: DataType | None = None
    meta: dict[str, Any] | None = None


class APIErrorDetail(BaseModel):
    field: str | None = None
    code: str | None = None
    message: str


class APIErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[APIErrorDetail] = Field(
        default_factory=list
    )


def success_response(
    *,
    data: Any = None,
    message: str = "Operation completed successfully.",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta,
    }


def error_response(
    *,
    message: str,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "errors": errors or [],
    }