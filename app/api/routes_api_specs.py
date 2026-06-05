"""API Specs routes — view generated OpenAPI specs."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import GeneratedApi
from app.schemas.common import ApiResponse
from app.schemas.workflow import ApiSpecSummary

router = APIRouter(prefix="/sites/{site_id}/api-specs", tags=["api-specs"])


@router.get("")
async def list_api_specs(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[list[ApiSpecSummary]]:
    result = await session.execute(
        select(GeneratedApi).where(GeneratedApi.site_id == site_id)
    )
    specs = result.scalars().all()
    summaries = [
        ApiSpecSummary(
            id=s.id,
            site_id=s.site_id,
            workflow_id=s.workflow_id,
            spec_json=s.spec_json,
            openapi_url=s.openapi_url,
            created_at=s.created_at,
        )
        for s in specs
    ]
    return ApiResponse.ok(summaries)