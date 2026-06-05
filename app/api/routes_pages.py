"""Pages API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Page
from app.schemas.common import ApiResponse
from app.schemas.page import PageListResponse, PageSummary

router = APIRouter(prefix="/sites/{site_id}/pages", tags=["pages"])


@router.get("")
async def list_pages(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[PageListResponse]:
    result = await session.execute(
        select(Page).where(Page.site_id == site_id).order_by(Page.depth)
    )
    pages = result.scalars().all()
    summaries = [
        PageSummary(
            id=p.id,
            url=p.url,
            canonical_url=p.canonical_url,
            title=p.title,
            depth=p.depth,
            path=p.path,
            status_code=p.status_code,
            has_form=p.has_form,
            has_auth_hint=p.has_auth_hint,
            created_at=p.created_at,
        )
        for p in pages
    ]
    return ApiResponse.ok(PageListResponse(pages=summaries, total=len(summaries)))