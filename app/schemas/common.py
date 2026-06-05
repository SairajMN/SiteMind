from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ErrorDetail | None = None

    @classmethod
    def ok(cls, data: T) -> "ApiResponse[T]":
        return cls(data=data, error=None)

    @classmethod
    def fail(
        cls,
        *,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> "ApiResponse[None]":
        return cls(
            data=None,
            error=ErrorDetail(code=code, message=message, details=details or {}),
        )
