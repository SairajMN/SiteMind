"""Workflow and API spec schemas."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel

class WorkflowStepSummary(BaseModel):
    id: uuid.UUID
    step_index: int = 0
    page_id: uuid.UUID | None = None
    action_type: str | None = None
    selector: str | None = None
    endpoint_id: uuid.UUID | None = None
    description: str | None = None
    confidence: float | None = None

class WorkflowSummary(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    name: str | None = None
    summary: str | None = None
    confidence: float | None = None
    steps: list[WorkflowStepSummary] = []
    created_at: datetime

class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowSummary]
    total: int

class ApiSpecSummary(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    workflow_id: uuid.UUID | None = None
    spec_json: dict[str, Any] | None = None
    openapi_url: str | None = None
    created_at: datetime
