"""DAG schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DagNodeSummary(BaseModel):
    id: uuid.UUID
    dag_run_id: uuid.UUID
    node_key: str
    node_type: str | None = None
    status: str
    attempt_count: int = 0
    lane: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_json: dict[str, Any] | None = None
    output_json: dict[str, Any] | None = None


class DagEdgeSummary(BaseModel):
    id: uuid.UUID
    dag_run_id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    edge_type: str | None = None


class DagRunDetail(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    crawl_job_id: uuid.UUID
    status: str
    planner_version: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    nodes: list[DagNodeSummary] = []
    edges: list[DagEdgeSummary] = []
    created_at: datetime