"""Comparison API route — runs the browser comparison agent and returns results."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from agent.orchestrator import run_query
from agent.metrics import get_metrics_collector
from app.schemas.common import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["comparison"])


class ComparisonRequest(BaseModel):
    query: str
    max_wall_clock_sec: float = 120.0


class ComparisonResult(BaseModel):
    status: str
    query: str
    wall_clock_ms: float
    iterations: int
    nodes: list[dict[str, Any]]
    final_answer: str | None = None
    critic_status: str | None = None
    comparison_table: list[dict[str, Any]] = []
    replay_filepath: str | None = None
    browser_actions: list[dict[str, Any]] = []
    screenshots: list[dict[str, Any]] = []
    selected_path: str | None = None
    metrics: dict[str, Any] = {}


@router.post("/comparison")
async def run_comparison(body: ComparisonRequest) -> ApiResponse[ComparisonResult]:
    """Run a browser comparison task."""
    try:
        result = await run_query(body.query)

        final_answer = result.final_answer
        critic_status = None
        comparison_items = []
        replay_filepath = None
        browser_actions = []
        screenshots = []
        selected_path = None

        for ns in result.nodes:
            output = ns.output or {}

            if ns.spec.key == "critic_agent":
                critic_status = output.get("status")

            elif ns.spec.key == "formatter":
                if not final_answer:
                    final_answer = output.get("answer")
                if output.get("answer"):
                    items = output.get("answer", "").split("\n")
                    for line in items:
                        if line.startswith("| ") and "Rank" not in line and "---" not in line:
                            parts = [p.strip() for p in line.split("|")[1:-1]]
                            if len(parts) >= 2:
                                comparison_items.append({
                                    "rank": parts[0] if len(parts) > 0 else "",
                                    "name": parts[1] if len(parts) > 1 else "",
                                    "likes": parts[2] if len(parts) > 2 else "",
                                    "downloads": parts[3] if len(parts) > 3 else "",
                                    "rating": parts[4] if len(parts) > 4 else "",
                                    "price": parts[5] if len(parts) > 5 else "",
                                    "source": parts[6] if len(parts) > 6 else "",
                                })

            elif ns.spec.key == "replay_generator":
                replay_filepath = output.get("replay_filepath")

            elif ns.spec.key == "browser_comparison":
                report_data = output.get("report_data", {})
                browser_actions = report_data.get("actions", [])
                screenshots = report_data.get("screenshots", [])
                selected_path = output.get("path")

        metrics_collector = get_metrics_collector()
        metrics = metrics_collector.get_summary()
        if isinstance(metrics, dict) and "message" in metrics:
            metrics = {}

        return ApiResponse.ok(ComparisonResult(
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
            critic_status=critic_status,
            comparison_table=comparison_items,
            replay_filepath=replay_filepath,
            browser_actions=browser_actions,
            screenshots=screenshots,
            selected_path=selected_path,
            metrics=metrics,
        ))

    except Exception as exc:
        logger.exception("Comparison failed: %s", exc)
        return ApiResponse.fail(code="COMPARISON_FAILED", message=str(exc))


def _preview_output(output: dict[str, Any] | None) -> dict[str, Any] | None:
    if not output:
        return None
    preview = {}
    for k, v in output.items():
        if k in ("report_data", "content", "html_snippet"):
            continue
        if isinstance(v, str) and len(v) > 200:
            preview[k] = v[:200] + "..."
        elif isinstance(v, list) and len(v) > 10:
            preview[k] = v[:10]
        else:
            preview[k] = v
    return preview
