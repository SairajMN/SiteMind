"""Q&A schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CitationSchema(BaseModel):
    source_url: str | None = None
    artifact_type: str | None = None
    snippet: str | None = None
    score: float | None = None
    confidence: float | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    artifact_types: list[str] | None = None


class AnswerResponse(BaseModel):
    answer_id: uuid.UUID
    site_id: uuid.UUID
    question: str
    answer_text: str | None = None
    confidence: float | None = None
    critic_status: str | None = None
    citations: list[CitationSchema] = []
    created_at: datetime


class CriticEventSchema(BaseModel):
    id: uuid.UUID
    status: str
    reason: str | None = None
    recovery_action: str | None = None
    created_at: datetime