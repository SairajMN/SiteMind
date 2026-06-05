from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import enqueue_job
from app.core.security import (
    SecurityError,
    clamp_depth,
    clamp_page_budget,
    extract_domain,
    validate_scope_policy,
    validate_target_url,
)
from app.models.orm import CrawlJob, DagRun, Site
from app.schemas.site import CreateSiteRequest, CreateSiteResponse

WORKER_QUEUE = "sitemind:crawl_jobs"


class IngestionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


async def create_site_and_job(
    session: AsyncSession,
    payload: CreateSiteRequest,
) -> CreateSiteResponse:
    settings = get_settings()
    try:
        root_url = validate_target_url(str(payload.url))
        scope_policy = validate_scope_policy(payload.scope_policy)
    except SecurityError as exc:
        raise IngestionError("INVALID_URL", str(exc)) from exc

    depth = clamp_depth(payload.crawl_depth, maximum=settings.crawl_max_depth)
    budget = clamp_page_budget(
        payload.page_budget, maximum=settings.crawl_max_page_budget
    )

    site = Site(
        root_url=root_url,
        domain=extract_domain(root_url),
        scope_policy=scope_policy,
    )
    session.add(site)
    await session.flush()

    job = CrawlJob(
        site_id=site.id,
        status="queued",
        goal=payload.goal,
        requested_depth=depth,
        page_budget=budget,
    )
    session.add(job)
    await session.flush()

    dag_run = DagRun(
        site_id=site.id,
        crawl_job_id=job.id,
        status="queued",
        planner_version="mvp-0",
    )
    session.add(dag_run)
    await session.flush()

    await enqueue_job(
        WORKER_QUEUE,
        {
            "site_id": str(site.id),
            "crawl_job_id": str(job.id),
            "dag_run_id": str(dag_run.id),
            "root_url": root_url,
            "goal": payload.goal,
            "requested_depth": depth,
            "page_budget": budget,
            "include_screenshots": payload.include_screenshots,
            "include_network_traces": payload.include_network_traces,
        },
    )

    return CreateSiteResponse(
        site_id=site.id,
        crawl_job_id=job.id,
        dag_run_id=dag_run.id,
        status=job.status,
    )


async def get_job_status(session: AsyncSession, job_id: uuid.UUID) -> CrawlJob | None:
    from sqlalchemy import select

    result = await session.execute(select(CrawlJob).where(CrawlJob.id == job_id))
    return result.scalar_one_or_none()


async def get_site(session: AsyncSession, site_id: uuid.UUID) -> Site | None:
    from sqlalchemy import select

    result = await session.execute(select(Site).where(Site.id == site_id))
    return result.scalar_one_or_none()
