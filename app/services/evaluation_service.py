"""Evaluation service — computes metrics after analysis runs."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import (
    Answer,
    Citation,
    DagNode,
    Endpoint,
    Evaluation,
    EvaluationMetric,
    Form,
    Page,
    RetrievalChunk,
    Workflow,
)

logger = logging.getLogger(__name__)


async def compute_evaluation_metrics(
    session: AsyncSession,
    site_id: uuid.UUID,
    crawl_job_id: uuid.UUID,
    dag_run_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Compute evaluation metrics for a completed analysis run."""
    eval_row = Evaluation(
        site_id=site_id,
        crawl_job_id=crawl_job_id,
        status="computing",
    )
    session.add(eval_row)
    await session.flush()

    metrics: dict[str, Any] = {}

    page_count = await session.scalar(
        select(func.count()).select_from(Page).where(Page.crawl_job_id == crawl_job_id)
    )
    metrics["pages_discovered"] = page_count or 0

    form_count = await session.scalar(
        select(func.count())
        .select_from(Form)
        .join(Page)
        .where(Page.crawl_job_id == crawl_job_id)
    )
    metrics["forms_found"] = form_count or 0

    ep_count = await session.scalar(
        select(func.count())
        .select_from(Endpoint)
        .join(Page)
        .where(Page.crawl_job_id == crawl_job_id)
    )
    metrics["endpoints_found"] = ep_count or 0

    wf_count = await session.scalar(
        select(func.count()).select_from(Workflow).where(Workflow.site_id == site_id)
    )
    metrics["workflows_found"] = wf_count or 0

    chunk_count = await session.scalar(
        select(func.count()).select_from(RetrievalChunk).where(RetrievalChunk.site_id == site_id)
    )
    metrics["chunks_indexed"] = chunk_count or 0

    answer_count = await session.scalar(
        select(func.count()).select_from(Answer).where(Answer.site_id == site_id)
    )
    citation_count = await session.scalar(
        select(func.count())
        .select_from(Citation)
        .join(Answer)
        .where(Answer.site_id == site_id)
    )
    metrics["answers_count"] = answer_count or 0
    metrics["citations_count"] = citation_count or 0
    metrics["citation_rate"] = (
        float(citation_count) / float(answer_count) if answer_count and answer_count > 0 else 0.0
    )

    if dag_run_id:
        node_count = await session.scalar(
            select(func.count()).select_from(DagNode).where(DagNode.dag_run_id == dag_run_id)
        )
        failed_count = await session.scalar(
            select(func.count())
            .select_from(DagNode)
            .where(DagNode.dag_run_id == dag_run_id, DagNode.status == "failed")
        )
        succeeded_count = await session.scalar(
            select(func.count())
            .select_from(DagNode)
            .where(DagNode.dag_run_id == dag_run_id, DagNode.status == "succeeded")
        )
        metrics["dag_nodes_total"] = node_count or 0
        metrics["dag_nodes_failed"] = failed_count or 0
        metrics["dag_nodes_succeeded"] = succeeded_count or 0
        metrics["dag_node_failure_rate"] = (
            float(failed_count) / float(node_count) if node_count and node_count > 0 else 0.0
        )

    avg_conf_result = await session.execute(
        select(func.avg(Answer.confidence)).where(Answer.site_id == site_id)
    )
    avg_conf = avg_conf_result.scalar()
    metrics["avg_answer_confidence"] = float(avg_conf) if avg_conf else 0.0

    for key, value in metrics.items():
        session.add(
            EvaluationMetric(
                evaluation_id=eval_row.id,
                metric_key=key,
                metric_value=float(value) if not isinstance(value, (int, float)) else float(value),
            )
        )

    eval_row.status = "completed"
    await session.flush()
    metrics["evaluation_id"] = str(eval_row.id)
    return metrics