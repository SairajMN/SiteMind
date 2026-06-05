"""Site DAG runner — orchestrates the real crawl→extract→index→evaluate pipeline."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dag.engine import DagEngine
from app.dag.planner import plan_site_crawl_dag
from app.models.orm import CrawlJob, DagNode, DagRun, Page, Site
from app.services.crawl_service import run_crawl
from app.services.retrieval_service import index_artifact, retrieve_evidence
from app.services.answer_service import generate_answer
from app.services.critic_service import verify_answer
from app.services.evaluation_service import compute_evaluation_metrics
from app.services.workflow_miner_service import mine_workflows
from app.services.api_generation_service import generate_api_specs
from app.services.screenshot_service import capture_and_analyze_screenshot
from app.services.network_trace_service import (
    capture_network_traces,
    extract_endpoint_candidates,
)
from app.models.orm import Endpoint, AuthSignal, EmbeddingsMetadata, RetrievalChunk

logger = logging.getLogger(__name__)


async def _persist_node(
    session: AsyncSession,
    dag_run: DagRun,
    key: str,
    node_type: str,
    lane: int,
    status: str,
    duration_ms: float | None,
    output: dict,
    error: str | None = None,
) -> None:
    row = DagNode(
        dag_run_id=dag_run.id,
        node_key=key,
        node_type=node_type,
        status=status,
        lane=str(lane),
        duration_ms=int(duration_ms) if duration_ms is not None else None,
        output_json=output,
        error_json={"message": error} if error else None,
        finished_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await session.flush()


async def run_site_dag(
    session: AsyncSession,
    *,
    site_id: uuid.UUID,
    crawl_job_id: uuid.UUID,
    dag_run_id: uuid.UUID,
) -> dict[str, Any]:
    site = await session.get(Site, site_id)
    job = await session.get(CrawlJob, crawl_job_id)
    dag_run = await session.get(DagRun, dag_run_id)
    if not site or not job or not dag_run:
        raise ValueError("Missing site, job, or dag_run")

    dag_run.status = "running"
    dag_run.started_at = datetime.now(timezone.utc)
    await session.flush()

    crawl_counts: dict[str, int] = {}
    _shared_pages: list[Page] = []

    async def planner(ctx: dict[str, Any]) -> dict[str, Any]:
        return {"planned": True, "nodes": 11}

    async def crawl(ctx: dict[str, Any]) -> dict[str, Any]:
        nonlocal crawl_counts
        crawl_counts = await run_crawl(session, site=site, job=job)
        return crawl_counts

    async def dom(ctx: dict[str, Any]) -> dict[str, Any]:
        """Extract DOM structure from crawled pages and index."""
        page_result = await session.execute(
            select(Page).where(Page.crawl_job_id == job.id)
        )
        pages = page_result.scalars().all()
        _shared_pages.extend(pages)
        chunk_total = 0
        for page in pages:
            text_parts = []
            if page.title:
                text_parts.append(f"Title: {page.title}")
            text_parts.append(f"URL: {page.url}")
            if page.path:
                text_parts.append(f"Path: {page.path}")
            text = "\n".join(text_parts)
            if len(text.strip()) < 3:
                continue
            n = await index_artifact(
                session, site.id, page.id, "page", text,
                source_url=page.url, title=page.title, confidence=0.85,
            )
            chunk_total += n
        return {"artifact_type": "dom", "pages_analyzed": len(pages), "chunks": chunk_total}

    async def form(ctx: dict[str, Any]) -> dict[str, Any]:
        """Extract and index forms from pages."""
        from app.models.orm import Form, FormField

        form_result = await session.execute(
            select(Form).join(Page).where(Page.crawl_job_id == job.id)
        )
        forms = form_result.scalars().all()
        chunk_total = 0
        for form in forms:
            field_result = await session.execute(
                select(FormField).where(FormField.form_id == form.id)
            )
            fields = field_result.scalars().all()
            text = f"Form action: {form.action_url or 'N/A'}, method: {form.method or 'GET'}"
            for f in fields:
                text += f"\n  Field: {f.name or 'unnamed'} ({f.field_type or 'text'})"
            page = await session.get(Page, form.page_id)
            n = await index_artifact(
                session, site.id, form.page_id, "form", text,
                source_url=page.url if page else None,
                title=f"Form: {form.action_url or 'unknown'}",
                confidence=form.confidence or 0.8,
            )
            chunk_total += n
        return {"artifact_type": "form", "count": len(forms), "chunks": chunk_total}

    async def endpoint(ctx: dict[str, Any]) -> dict[str, Any]:
        """Index endpoint candidates."""
        ep_result = await session.execute(
            select(Endpoint).join(Page).where(Page.crawl_job_id == job.id)
        )
        endpoints = ep_result.scalars().all()
        chunk_total = 0
        for ep in endpoints:
            text = f"Endpoint: {ep.method or 'GET'} {ep.request_url}, type: {ep.request_type or 'api'}"
            page = await session.get(Page, ep.page_id)
            n = await index_artifact(
                session, site.id, ep.page_id, "endpoint", text,
                source_url=ep.request_url,
                title=f"{ep.method or 'GET'} {ep.request_url}",
                confidence=ep.confidence or 0.7,
            )
            chunk_total += n
        return {"artifact_type": "endpoint", "count": len(endpoints), "chunks": chunk_total}

    async def auth(ctx: dict[str, Any]) -> dict[str, Any]:
        """Index auth signals."""
        auth_result = await session.execute(
            select(AuthSignal).join(Page).where(Page.crawl_job_id == job.id)
        )
        auth_signals = auth_result.scalars().all()
        chunk_total = 0
        for a in auth_signals:
            text = f"Auth signal: {a.signal_type}, value: {a.signal_value or 'N/A'}"
            page = await session.get(Page, a.page_id)
            n = await index_artifact(
                session, site.id, a.page_id, "auth", text,
                source_url=page.url if page else None,
                title=f"Auth: {a.signal_type}",
                confidence=a.confidence or 0.7,
            )
            chunk_total += n
        return {"artifact_type": "auth", "count": len(auth_signals), "chunks": chunk_total}

    async def screenshot(ctx: dict[str, Any]) -> dict[str, Any]:
        """Capture and analyze screenshots."""
        page_result = await session.execute(
            select(Page).where(Page.crawl_job_id == job.id).limit(3)
        )
        pages = page_result.scalars().all()
        results = []
        for page in pages:
            result = await capture_and_analyze_screenshot(page.url, page.id)
            if not result.get("skipped", True):
                n = await index_artifact(
                    session, site.id, page.id, "screenshot", result.get("summary", ""),
                    source_url=page.url, title=f"Screenshot: {page.title or page.url}",
                    confidence=0.6,
                )
                result["chunks"] = n
            results.append(result)
        return {"screenshots": results, "count": len(results)}

    async def network_trace(ctx: dict[str, Any]) -> dict[str, Any]:
        """Capture network traces and extract endpoint candidates."""
        page_result = await session.execute(
            select(Page).where(Page.crawl_job_id == job.id).limit(3)
        )
        pages = page_result.scalars().all()
        all_traces = []
        all_candidates = []
        for page in pages:
            traces = await capture_network_traces(page.url, page.id)
            all_traces.extend(traces)
            candidates = extract_endpoint_candidates(traces)
            for c in candidates:
                ep = Endpoint(
                    page_id=page.id,
                    request_url=c["request_url"],
                    method=c["method"],
                    request_type=c["request_type"],
                    status_code=c.get("status_code"),
                    confidence=c["confidence"],
                    observation_type=c.get("observation_type", "network_trace"),
                )
                session.add(ep)
                all_candidates.append(c)
        await session.flush()
        return {"traces": len(all_traces), "endpoint_candidates": len(all_candidates)}

    async def workflow_miner(ctx: dict[str, Any]) -> dict[str, Any]:
        """Mine workflows from collected artifacts."""
        from app.models.orm import Workflow as WFModel

        wfs = await mine_workflows(session, site.id, job.id)
        # Index workflow chunks
        wf_rows = (await session.execute(select(WFModel).where(WFModel.site_id == site.id))).scalars().all()
        for wf in wf_rows:
            text = f"Workflow: {wf.name or 'Untitled'}\n{wf.summary or ''}"
            await index_artifact(
                session, site.id, None, "workflow", text,
                title=wf.name or "Workflow",
                confidence=wf.confidence or 0.7,
            )
        return {"workflows": len(wfs), "details": wfs}

    async def knowledge_builder(ctx: dict[str, Any]) -> dict[str, Any]:
        """Aggregate all artifacts into retrieval index."""
        # Pages already indexed via individual extractors
        chunk_result = await session.execute(
            select(RetrievalChunk).where(RetrievalChunk.site_id == site.id)
        )
        chunks = chunk_result.scalars().all()
        return {"chunks": len(chunks)}

    async def api_generator(ctx: dict[str, Any]) -> dict[str, Any]:
        """Generate API specs from workflows."""
        specs = await generate_api_specs(session, site.id)
        return {"specs": len(specs), "details": specs}

    async def evaluation(ctx: dict[str, Any]) -> dict[str, Any]:
        """Compute evaluation metrics."""
        metrics = await compute_evaluation_metrics(
            session, site.id, job.id, dag_run.id
        )
        return metrics

    handlers = {
        "planner": planner,
        "crawl": crawl,
        "dom": dom,
        "form": form,
        "endpoint": endpoint,
        "auth": auth,
        "screenshot": screenshot,
        "network_trace": network_trace,
        "workflow_miner": workflow_miner,
        "knowledge_builder": knowledge_builder,
        "api_generator": api_generator,
        "evaluation": evaluation,
    }

    nodes, edges = plan_site_crawl_dag(handlers)
    engine = DagEngine(max_parallel=6)
    result = await engine.run(site.root_url, nodes, edges, {"site_id": str(site_id)})

    for ns in result.nodes:
        await _persist_node(
            session,
            dag_run,
            ns.spec.key,
            ns.spec.node_type,
            ns.spec.lane,
            ns.status.value,
            ns.duration_ms,
            ns.output,
            ns.error,
        )

    dag_run.status = result.status
    dag_run.finished_at = datetime.now(timezone.utc)

    # Update job status
    if result.status == "succeeded":
        job.status = "completed"
    elif result.status == "failed":
        job.status = "failed"
    job.finished_at = datetime.now(timezone.utc)

    await session.commit()
    return {
        "status": result.status,
        "wall_clock_ms": result.wall_clock_ms,
        "crawl_counts": crawl_counts,
        "parallel_layers": result.metadata.get("parallel_layers"),
    }