"""Form schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class FormFieldSummary(BaseModel):
    id: uuid.UUID
    name: str | None = None
    label: str | None = None
    field_type: str | None = None
    required: bool = False
    placeholder: str | None = None


class FormSummary(BaseModel):
    id: uuid.UUID
    page_id: uuid.UUID
    form_index: int = 0
    action_url: str | None = None
    method: str | None = None
    form_name: str | None = None
    confidence: float | None = None
    fields: list[FormFieldSummary] = []
    created_at: datetime


class FormListResponse(BaseModel):
    forms: list[FormSummary]
    total: int