"""Workflow miner — infers multi-step workflows from pages, forms, and endpoints."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import (
    AuthSignal,
    Endpoint,
    Form,
    Page,
    Workflow,
    WorkflowStep,
)

logger = logging.getLogger(__name__)


async def mine_workflows(
    session: AsyncSession,
    site_id: uuid.UUID,
    crawl_job_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Infer workflows from pages with forms, endpoints, and auth signals."""
    workflows: list[dict[str, Any]] = []

    page_result = await session.execute(
        select(Page).where(Page.crawl_job_id == crawl_job_id).order_by(Page.depth)
    )
    pages = page_result.scalars().all()

    form_result = await session.execute(
        select(Form).join(Page).where(Page.crawl_job_id == crawl_job_id)
    )
    forms = form_result.scalars().all()

    ep_result = await session.execute(
        select(Endpoint).join(Page).where(Page.crawl_job_id == crawl_job_id)
    )
    endpoints = ep_result.scalars().all()

    auth_result = await session.execute(
        select(AuthSignal).join(Page).where(Page.crawl_job_id == crawl_job_id)
    )
    auth_signals = auth_result.scalars().all()

    form_map: dict[uuid.UUID, list[Form]] = {}
    for f in forms:
        form_map.setdefault(f.page_id, []).append(f)

    endpoint_map: dict[uuid.UUID, list[Endpoint]] = {}
    for ep in endpoints:
        endpoint_map.setdefault(ep.page_id, []).append(ep)

    auth_map: dict[uuid.UUID, list[AuthSignal]] = {}
    for a in auth_signals:
        auth_map.setdefault(a.page_id, []).append(a)

    # Login workflows
    login_pages = [p for p in pages if p.has_auth_hint]
    for lp in login_pages:
        wf_name = f"Login: {lp.title or lp.path or lp.url}"
        wf = Workflow(
            site_id=site_id,
            name=wf_name,
            summary=f"Authentication flow detected on {lp.url}",
            confidence=0.7,
        )
        session.add(wf)
        await session.flush()

        step_index = 0
        ws = WorkflowStep(
            workflow_id=wf.id,
            step_index=step_index,
            page_id=lp.id,
            action_type="navigate",
            description=f"Navigate to {lp.url}",
            confidence=0.8,
        )
        session.add(ws)
        step_index += 1

        for form in form_map.get(lp.id, []):
            ws = WorkflowStep(
                workflow_id=wf.id,
                step_index=step_index,
                page_id=lp.id,
                action_type="fill_form",
                description=f"Fill form: {form.action_url or 'unknown action'}",
                confidence=form.confidence or 0.7,
            )
            session.add(ws)
            step_index += 1

        for auth in auth_map.get(lp.id, []):
            ws = WorkflowStep(
                workflow_id=wf.id,
                step_index=step_index,
                page_id=lp.id,
                action_type="authenticate",
                description=f"Auth signal: {auth.signal_type}",
                confidence=auth.confidence or 0.6,
            )
            session.add(ws)
            step_index += 1

        submit_eps = [ep for ep in endpoint_map.get(lp.id, []) if ep.method in ("POST", "PUT")]
        for ep in submit_eps:
            ws = WorkflowStep(
                workflow_id=wf.id,
                step_index=step_index,
                page_id=lp.id,
                action_type="api_call",
                description=f"{ep.method} {ep.request_url}",
                endpoint_id=ep.id,
                confidence=ep.confidence or 0.6,
            )
            session.add(ws)
            step_index += 1

        workflows.append({
            "id": str(wf.id),
            "name": wf_name,
            "steps": step_index,
            "confidence": 0.7,
        })

    # Form submission workflows
    form_pages = [p for p in pages if p.has_form and not p.has_auth_hint]
    for fp in form_pages[:5]:
        page_forms = form_map.get(fp.id, [])
        if not page_forms:
            continue
        wf_name = f"Form: {fp.title or fp.path or 'unknown'}"

        wf = Workflow(
            site_id=site_id,
            name=wf_name,
            summary=f"Form interaction on {fp.url}",
            confidence=0.75,
        )
        session.add(wf)
        await session.flush()

        step_index = 0
        ws = WorkflowStep(
            workflow_id=wf.id,
            step_index=step_index,
            page_id=fp.id,
            action_type="navigate",
            description=f"Navigate to {fp.url}",
            confidence=0.85,
        )
        session.add(ws)
        step_index += 1

        for form in page_forms:
            ws = WorkflowStep(
                workflow_id=wf.id,
                step_index=step_index,
                page_id=fp.id,
                action_type="fill_form",
                description=f"Submit form to {form.action_url or 'unknown'} via {form.method or 'GET'}",
                confidence=form.confidence or 0.7,
            )
            session.add(ws)
            step_index += 1

        wf_eps = [ep for ep in endpoint_map.get(fp.id, []) if ep.method in ("POST", "PUT")]
        for ep in wf_eps:
            ws = WorkflowStep(
                workflow_id=wf.id,
                step_index=step_index,
                page_id=fp.id,
                action_type="api_call",
                description=f"{ep.method} {ep.request_url}",
                endpoint_id=ep.id,
                confidence=ep.confidence or 0.6,
            )
            session.add(ws)
            step_index += 1

        workflows.append({
            "id": str(wf.id),
            "name": wf_name,
            "steps": step_index,
            "confidence": 0.75,
        })

    await session.flush()
    logger.info("Mined %d workflows for site %s", len(workflows), site_id)
    return workflows