"""Endpoint schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class EndpointSummary(BaseModel):
    id: uuid.UUID
    page_id: uuid.UUID
    request_url: str
    method: str | None = None
    request_type: str | None = None
    status_code: int | None = None
    confidence: float | None = None
    observation_type: str | None = None
    created_at: datetime


class EndpointListResponse(BaseModel):
    endpoints: list[EndpointSummary]
    total: int