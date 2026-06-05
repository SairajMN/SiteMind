"""Workflows API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Workflow, WorkflowStep
from app.schemas.common import ApiResponse
from app.schemas.workflow import (
    WorkflowListResponse,
    WorkflowStepSummary,
    WorkflowSummary,
)

router = APIRouter(prefix="/sites/{site_id}/workflows", tags=["workflows"])


@router.get("")
async def list_workflows(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[WorkflowListResponse]:
    result = await session.execute(
        select(Workflow).where(Workflow.site_id == site_id)
    )
    workflows = result.scalars().all()
    summaries = []
    for wf in workflows:
        step_result = await session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == wf.id)
            .order_by(WorkflowStep.step_index)
        )
        steps = step_result.scalars().all()
        summaries.append(
            WorkflowSummary(
                id=wf.id,
                site_id=wf.site_id,
                name=wf.name,
                summary=wf.summary,
                confidence=wf.confidence,
                steps=[
                    WorkflowStepSummary(
                        id=s.id,
                        step_index=s.step_index,
                        page_id=s.page_id,
                        action_type=s.action_type,
                        selector=s.selector,
                        endpoint_id=s.endpoint_id,
                        description=s.description,
                        confidence=s.confidence,
                    )
                    for s in steps
                ],
                created_at=wf.created_at,
            )
        )
    return ApiResponse.ok(WorkflowListResponse(workflows=summaries, total=len(summaries)))