from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.site import JobProgress, JobStatusResponse
from app.services.ingestion_service import get_job_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[JobStatusResponse]:
    job = await get_job_status(session, job_id)
    if job is None:
        return ApiResponse.fail(code="NOT_FOUND", message="Job not found")

    progress = JobProgress()
    return ApiResponse.ok(
        JobStatusResponse(
            job_id=job.id,
            site_id=job.site_id,
            status=job.status,
            progress=progress,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_summary=job.error_summary,
        )
    )


@router.get("/{job_id}/events")
async def job_events(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    import asyncio
    import json

    from fastapi.responses import StreamingResponse

    async def stream():
        last: str | None = None
        for _ in range(600):
            job = await get_job_status(session, job_id)
            if job is None:
                yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"
                return
            payload = json.dumps({"job_id": str(job.id), "status": job.status})
            if payload != last:
                yield f"event: job.status\ndata: {payload}\n\n"
                yield f"event: job.progress\ndata: {payload}\n\n"
                last = payload
            if job.status in ("completed", "failed", "blocked"):
                break
            await asyncio.sleep(2)
        yield f"event: done\ndata: {json.dumps({'job_id': str(job_id)})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
