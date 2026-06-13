"""Web Search API route — searches the web with VLM + DOM analysis."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from agent.orchestrator import run_web_search
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["web_search"])


class WebSearchRequest(BaseModel):
    query: str
    max_wall_clock_sec: float = 120.0


class WebSearchItem(BaseModel):
    rank: str = ""
    name: str = ""
    price: str = ""
    rating: str = ""
    specs: str = ""
    source: str = ""
    page_title: str = ""


class WebSearchResult(BaseModel):
    status: str
    query: str
    wall_clock_ms: float
    iterations: int
    nodes: list[dict[str, Any]]
    final_answer: str | None = None
    comparison_table: list[dict[str, Any]] = []
    total_items: int = 0
    total_pages: int = 0
    metrics: dict[str, Any] = {}


@router.post("/web-search")
async def run_web_search_endpoint(body: WebSearchRequest) -> ApiResponse[WebSearchResult]:
    """Run a web search + VLM analysis. Accept any query."""
    try:
        result = await run_web_search(body.query)

        # Extract output from the formatter node
        final_answer = None
        comparison_table = []
        total_items = 0
        total_pages = 0

        for ns in result.nodes:
            output = ns.output or {}

            if ns.spec.key == "formatter":
                final_answer = output.get("answer")
                comparison_table = output.get("comparison_table", [])
                total_items = output.get("total_items", 0)
                total_pages = output.get("total_pages", 0)

        metrics = {}
        for ns in result.nodes:
            if ns.spec.key == "planner":
                continue
            metrics[f"{ns.spec.key}_duration_ms"] = ns.duration_ms
            metrics[f"{ns.spec.key}_status"] = ns.status.value

        return ApiResponse.ok(WebSearchResult(
            status=result.status,
            query=body.query,
            wall_clock_ms=result.wall_clock_ms,
            iterations=result.iteration_count,
            nodes=[
                {
                    "key": ns.spec.key,
                    "type": ns.spec.node_type,
                    "status": ns.status.value,
                    "duration_ms": ns.duration_ms,
                    "lane": ns.spec.lane,
                    "error": ns.error,
                    "output_preview": _preview_output(ns.output),
                }
                for ns in result.nodes
            ],
            final_answer=final_answer,
            comparison_table=comparison_table,
            total_items=total_items,
            total_pages=total_pages,
            metrics=metrics,
        ))

    except Exception as exc:
        logger.exception("Web search failed: %s", exc)
        return ApiResponse.fail(code="WEB_SEARCH_FAILED", message=str(exc))


def _preview_output(output: dict[str, Any] | None) -> dict[str, Any] | None:
    if not output:
        return None
    preview = {}
    for k, v in output.items():
        if k in ("report_data", "content", "html_snippet", "screenshot_b64"):
            continue
        if isinstance(v, str) and len(v) > 200:
            preview[k] = v[:200] + "..."
        elif isinstance(v, list) and len(v) > 10:
            preview[k] = v[:10]
        elif isinstance(v, dict) and "screenshot_b64" in v:
            preview[k] = {kk: vv for kk, vv in v.items() if kk != "screenshot_b64"}
        else:
            preview[k] = v
    return preview