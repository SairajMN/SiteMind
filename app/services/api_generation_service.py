"""API generation service — converts workflows to OpenAPI-like JSON."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.orm import Endpoint, GeneratedApi, Workflow, WorkflowStep

logger = logging.getLogger(__name__)


async def generate_api_specs(
    session: AsyncSession,
    site_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Generate OpenAPI-like specs from workflows and endpoints."""
    specs: list[dict[str, Any]] = []

    wf_result = await session.execute(
        select(Workflow).where(Workflow.site_id == site_id)
    )
    workflows = wf_result.scalars().all()

    for wf in workflows:
        step_result = await session.execute(
            select(WorkflowStep)
            .where(WorkflowStep.workflow_id == wf.id)
            .order_by(WorkflowStep.step_index)
        )
        steps = step_result.scalars().all()

        paths: dict[str, dict[str, Any]] = {}
        for step in steps:
            if step.endpoint_id:
                ep = await session.get(Endpoint, step.endpoint_id)
                if not ep:
                    continue
                method = (ep.method or "GET").lower()
                path = ep.request_url
                paths[path] = {
                    method: {
                        "summary": step.description or f"Step {step.step_index}",
                        "operationId": f"step_{step.step_index}",
                        "parameters": [
                            {
                                "name": "step_index",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {"200": {"description": "Successful response"}},
                        "x-confidence": step.confidence or 0.5,
                        "x-inferred": True,
                    }
                }

        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": wf.name or "Inferred Workflow API",
                "description": wf.summary or "Auto-generated from workflow analysis",
                "version": "1.0.0",
                "x-confidence": wf.confidence or 0.5,
                "x-inferred": True,
            },
            "paths": paths,
            "x-workflow_id": str(wf.id),
            "x-site_id": str(site_id),
        }

        api_row = GeneratedApi(
            site_id=site_id,
            workflow_id=wf.id,
            spec_json=spec,
            openapi_url=None,
        )
        session.add(api_row)
        await session.flush()

        specs.append({
            "id": str(api_row.id),
            "workflow_id": str(wf.id),
            "spec": spec,
            "endpoint_count": len(paths),
        })

    logger.info("Generated %d API specs for site %s", len(specs), site_id)
    return specs