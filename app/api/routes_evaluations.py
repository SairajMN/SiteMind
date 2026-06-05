"""Evaluations API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Evaluation, EvaluationMetric
from app.schemas.common import ApiResponse
from app.schemas.evaluation import EvaluationListResponse, EvaluationSummary, MetricSchema

router = APIRouter(prefix="/sites/{site_id}/evaluations", tags=["evaluations"])


@router.get("")
async def list_evaluations(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[EvaluationListResponse]:
    result = await session.execute(
        select(Evaluation).where(Evaluation.site_id == site_id).order_by(Evaluation.created_at.desc())
    )
    evaluations = result.scalars().all()
    summaries = []
    for ev in evaluations:
        metric_result = await session.execute(
            select(EvaluationMetric).where(EvaluationMetric.evaluation_id == ev.id)
        )
        metrics = metric_result.scalars().all()
        summaries.append(
            EvaluationSummary(
                id=ev.id,
                site_id=ev.site_id,
                crawl_job_id=ev.crawl_job_id,
                status=ev.status,
                metrics=[
                    MetricSchema(
                        metric_key=m.metric_key,
                        metric_value=m.metric_value,
                        details_json=m.details_json,
                    )
                    for m in metrics
                ],
                created_at=ev.created_at,
            )
        )
    return ApiResponse.ok(EvaluationListResponse(evaluations=summaries, total=len(summaries)))