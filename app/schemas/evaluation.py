"""Evaluation schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class MetricSchema(BaseModel):
    metric_key: str
    metric_value: float | None = None
    details_json: dict[str, Any] | None = None


class EvaluationSummary(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    crawl_job_id: uuid.UUID | None = None
    status: str
    metrics: list[MetricSchema] = []
    created_at: datetime


class EvaluationListResponse(BaseModel):
    evaluations: list[EvaluationSummary]
    total: int