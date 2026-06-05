"""Endpoints API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Endpoint, Page
from app.schemas.common import ApiResponse
from app.schemas.endpoint import EndpointListResponse, EndpointSummary

router = APIRouter(prefix="/sites/{site_id}/endpoints", tags=["endpoints"])


@router.get("")
async def list_endpoints(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[EndpointListResponse]:
    result = await session.execute(
        select(Endpoint).join(Page).where(Page.site_id == site_id)
    )
    endpoints = result.scalars().all()
    summaries = [
        EndpointSummary(
            id=e.id, page_id=e.page_id, request_url=e.request_url,
            method=e.method, request_type=e.request_type,
            status_code=e.status_code, confidence=e.confidence,
            observation_type=e.observation_type, created_at=e.created_at,
        )
        for e in endpoints
    ]
    return ApiResponse.ok(EndpointListResponse(endpoints=summaries, total=len(summaries)))