"""Page schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class PageSummary(BaseModel):
    id: uuid.UUID
    url: str
    canonical_url: str | None = None
    title: str | None = None
    depth: int = 0
    path: str | None = None
    status_code: int | None = None
    has_form: bool = False
    has_auth_hint: bool = False
    created_at: datetime


class PageListResponse(BaseModel):
    pages: list[PageSummary]
    total: int