from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter, sites_post_limit
from app.models.orm import CrawlJob, Site
from app.schemas.common import ApiResponse
from app.schemas.site import (
    AskRequest,
    AskResponseStub,
    CreateSiteRequest,
    CreateSiteResponse,
    SiteSummary,
)
from app.services.ingestion_service import IngestionError, create_site_and_job, get_site
from app.core.rate_limit import ask_limit

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit(sites_post_limit())
async def create_site(
    request: Request,
    body: CreateSiteRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[CreateSiteResponse]:
    try:
        result = await create_site_and_job(session, body)
    except IngestionError as exc:
        return ApiResponse.fail(code=exc.code, message=exc.message)
    return ApiResponse.ok(result)


@router.get("/{site_id}")
async def get_site_detail(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[SiteSummary]:
    site = await get_site(session, site_id)
    if site is None:
        return ApiResponse.fail(code="NOT_FOUND", message="Site not found")

    job_result = await session.execute(
        select(CrawlJob)
        .where(CrawlJob.site_id == site_id)
        .order_by(CrawlJob.created_at.desc())
        .limit(1)
    )
    latest = job_result.scalar_one_or_none()

    return ApiResponse.ok(
        SiteSummary(
            site_id=site.id,
            root_url=site.root_url,
            domain=site.domain,
            scope_policy=site.scope_policy,
            latest_job_id=latest.id if latest else None,
            latest_job_status=latest.status if latest else None,
            created_at=site.created_at,
        )
    )


@router.post("/{site_id}/ask")
@limiter.limit(ask_limit())
async def ask_site(
    request: Request,
    site_id: uuid.UUID,
    body: AskRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[AskResponseStub]:
    site = await get_site(session, site_id)
    if site is None:
        return ApiResponse.fail(code="NOT_FOUND", message="Site not found")
    return ApiResponse.ok(
        AskResponseStub(
            site_id=site_id,
            message="Q&A pipeline not implemented in scaffold",
        )
    )
