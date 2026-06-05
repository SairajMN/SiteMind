"""DAG run API routes — view execution graph."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import DagEdge, DagNode, DagRun
from app.schemas.common import ApiResponse
from app.schemas.dag import DagEdgeSummary, DagNodeSummary, DagRunDetail

router = APIRouter(prefix="/dag-runs", tags=["dag"])


@router.get("/{dag_run_id}")
async def get_dag_run(
    dag_run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[DagRunDetail]:
    dag_run = await session.get(DagRun, dag_run_id)
    if dag_run is None:
        return ApiResponse.fail(code="NOT_FOUND", message="DAG run not found")

    node_result = await session.execute(
        select(DagNode).where(DagNode.dag_run_id == dag_run_id)
    )
    nodes = node_result.scalars().all()

    edge_result = await session.execute(
        select(DagEdge).where(DagEdge.dag_run_id == dag_run_id)
    )
    edges = edge_result.scalars().all()

    return ApiResponse.ok(
        DagRunDetail(
            id=dag_run.id,
            site_id=dag_run.site_id,
            crawl_job_id=dag_run.crawl_job_id,
            status=dag_run.status,
            planner_version=dag_run.planner_version,
            started_at=dag_run.started_at,
            finished_at=dag_run.finished_at,
            nodes=[
                DagNodeSummary(
                    id=n.id,
                    dag_run_id=n.dag_run_id,
                    node_key=n.node_key,
                    node_type=n.node_type,
                    status=n.status,
                    attempt_count=n.attempt_count,
                    lane=n.lane,
                    started_at=n.started_at,
                    finished_at=n.finished_at,
                    duration_ms=n.duration_ms,
                    error_json=n.error_json,
                    output_json=n.output_json,
                )
                for n in nodes
            ],
            edges=[
                DagEdgeSummary(
                    id=e.id,
                    dag_run_id=e.dag_run_id,
                    from_node_id=e.from_node_id,
                    to_node_id=e.to_node_id,
                    edge_type=e.edge_type,
                )
                for e in edges
            ],
            created_at=dag_run.created_at,
        )
    )