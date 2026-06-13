from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import yaml

from agent.handlers import build_handlers, mock_evidence
from app.dag.engine import DagEngine
from app.dag.models import DagRunResult, NodeState, NodeStatus
from app.dag.planner import plan_agent_query_dag, plan_comparison_dag, plan_web_search_dag

logger = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).parent / "agent_config.yaml"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


async def run_web_search(
    query: str,
    *,
    max_iterations: int | None = None,
    max_wall_clock_sec: float | None = None,
) -> DagRunResult:
    """Run a web search + VLM analysis query through the DAG."""
    config = load_config()
    orch = config.get("orchestrator", {})
    handlers = build_handlers()
    nodes, edges = plan_web_search_dag(handlers)

    ctx: dict[str, Any] = {
        "query": query,
        "query_kind": "web_search",
    }

    engine = DagEngine(max_parallel=orch.get("max_parallel", 8))
    result = await engine.run(query, nodes, edges, ctx)

    max_iter = max_iterations or orch.get("default_max_iterations", 10)
    max_wall = max_wall_clock_sec or orch.get("default_max_wall_clock_sec", 120)
    result.metadata["bounds"] = {
        "max_iterations": max_iter,
        "max_wall_clock_sec": max_wall,
        "iterations_ok": result.iteration_count <= max_iter,
        "wall_clock_ok": (result.wall_clock_ms / 1000) <= max_wall,
    }
    result.metadata["query_kind"] = "web_search"
    return result


def _classify_query(query: str, config: dict[str, Any]) -> tuple[str, str | None]:
    q = query.strip()
    for item in config.get("base_queries", []):
        if item["query"] == q:
            return "base", item["id"]
    if "parallel" in q.lower() and "parallel" in config.get("assignment_queries", {}):
        return "parallel_fanout", None
    assign = config.get("assignment_queries", {})
    if q == assign.get("critic_demo", {}).get("query"):
        return "critic", None
    if q == assign.get("coder_demo", {}).get("query"):
        return "coder", None
    if q == assign.get("investigator_demo", {}).get("query"):
        return "investigator", None
    # fuzzy
    if "parallel" in q.lower():
        return "parallel_fanout", None
    if "form" in q.lower():
        return "critic", None
    if "median depth" in q.lower():
        return "coder", None
    if "investigate" in q.lower():
        return "investigator", None
    # Comparison queries
    comparison_keywords = ["compare", "comparison", "vs", "versus", "top models",
                           "top products", "sorted by", "rank", "huggingface"]
    if any(kw in q.lower() for kw in comparison_keywords):
        return "comparison", None
    return "base", q if q in ("hello", "A", "I", "J", "K") else "hello"


async def run_query(
    query: str,
    *,
    evidence: dict[str, Any] | None = None,
    critic_force_fail: bool = False,
    max_iterations: int | None = None,
    max_wall_clock_sec: float | None = None,
) -> DagRunResult:
    config = load_config()
    orch = config.get("orchestrator", {})
    query_kind, base_id = _classify_query(query, config)

    handlers = build_handlers()
    if query_kind == "comparison":
        nodes, edges = plan_comparison_dag(handlers)
        ctx: dict[str, Any] = {
            "evidence": evidence or mock_evidence(),
            "query_kind": query_kind,
            "base_id": base_id,
            "critic_force_fail": critic_force_fail,
        }
        engine = DagEngine(max_parallel=orch.get("max_parallel", 8))
        result = await engine.run(query, nodes, edges, ctx)

        max_iter = max_iterations or orch.get("default_max_iterations", 10)
        max_wall = max_wall_clock_sec or orch.get("default_max_wall_clock_sec", 30)
        result.metadata["bounds"] = {
            "max_iterations": max_iter,
            "max_wall_clock_sec": max_wall,
            "iterations_ok": result.iteration_count <= max_iter,
            "wall_clock_ok": (result.wall_clock_ms / 1000) <= max_wall,
        }
        result.metadata["query_kind"] = query_kind
        result.metadata["critic_force_fail"] = critic_force_fail
        return result

    nodes, edges = plan_agent_query_dag(handlers, query_kind)

    ctx: dict[str, Any] = {
        "evidence": evidence or mock_evidence(),
        "query_kind": query_kind,
        "base_id": base_id,
        "critic_force_fail": critic_force_fail,
    }

    engine = DagEngine(max_parallel=orch.get("max_parallel", 8))
    result = await engine.run(query, nodes, edges, ctx)

    # Attach branch timings for parallel proof
    if query_kind == "parallel_fanout":
        timings = {}
        for ns in result.nodes:
            if ns.spec.key.startswith("branch_"):
                timings[ns.spec.key] = ns.duration_ms
        if "merge" in {ns.spec.key: ns for ns in result.nodes}:
            merge_state = next(n for n in result.nodes if n.spec.key == "merge")
            if merge_state.status == NodeStatus.SUCCEEDED:
                merge_state.output.setdefault("parallel_proof", {})["branch_durations_ms"] = list(
                    timings.values()
                )

    max_iter = max_iterations or orch.get("default_max_iterations", 10)
    max_wall = max_wall_clock_sec or orch.get("default_max_wall_clock_sec", 30)

    result.metadata["bounds"] = {
        "max_iterations": max_iter,
        "max_wall_clock_sec": max_wall,
        "iterations_ok": result.iteration_count <= max_iter,
        "wall_clock_ok": (result.wall_clock_ms / 1000) <= max_wall,
    }
    result.metadata["query_kind"] = query_kind
    result.metadata["critic_force_fail"] = critic_force_fail
    return result


def format_run_log(result: DagRunResult) -> str:
    lines = [
        f"query={result.query!r} status={result.status}",
        f"wall_clock_ms={result.wall_clock_ms:.2f} iterations={result.iteration_count}",
        f"answer={result.final_answer!r}",
        f"bounds={result.metadata.get('bounds')}",
    ]
    for ns in result.nodes:
        lines.append(
            f"  node={ns.spec.key} status={ns.status.value} "
            f"duration_ms={ns.duration_ms} lane={ns.spec.lane}"
        )
    layers = result.metadata.get("parallel_layers")
    if layers:
        lines.append(f"parallel_layers={layers}")
    return "\n".join(lines)
