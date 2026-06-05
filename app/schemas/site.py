from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class CreateSiteRequest(BaseModel):
    url: HttpUrl
    goal: str = "Analyze website structure and workflows"
    scope_policy: Literal["same_domain"] = "same_domain"
    crawl_depth: int = Field(default=3, ge=1, le=10)
    page_budget: int = Field(default=60, ge=1, le=500)
    include_screenshots: bool = True
    include_network_traces: bool = True


class CreateSiteResponse(BaseModel):
    site_id: uuid.UUID
    crawl_job_id: uuid.UUID
    dag_run_id: uuid.UUID
    status: str


class SiteSummary(BaseModel):
    site_id: uuid.UUID
    root_url: str
    domain: str
    scope_policy: str
    latest_job_id: uuid.UUID | None = None
    latest_job_status: str | None = None
    created_at: datetime


class JobProgress(BaseModel):
    pages_discovered: int = 0
    pages_processed: int = 0
    chunks_indexed: int = 0
    forms_found: int = 0
    endpoints_found: int = 0
    workflows_found: int = 0


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    site_id: uuid.UUID
    status: str
    progress: JobProgress
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AskResponseStub(BaseModel):
    site_id: uuid.UUID
    status: str = "not_implemented"
    message: str
