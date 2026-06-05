from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from app.dag.models import DagRunResult, EdgeSpec, NodeSpec, NodeState, NodeStatus

logger = logging.getLogger(__name__)


class DagEngine:
    """Minimal asyncio DAG executor with parallel fan-out and per-node timing."""

    def __init__(self, max_parallel: int = 8) -> None:
        self.max_parallel = max_parallel
        self._sem = asyncio.Semaphore(max_parallel)

    async def run(
        self,
        query: str,
        nodes: list[NodeSpec],
        edges: list[EdgeSpec],
        context: dict[str, Any],
    ) -> DagRunResult:
        run_id = str(uuid.uuid4())
        states: dict[str, NodeState] = {n.key: NodeState(spec=n) for n in nodes}
        deps: dict[str, set[str]] = {n.key: set() for n in nodes}
        rev_deps: dict[str, set[str]] = {n.key: set() for n in nodes}
        for e in edges:
            deps[e.to_key].add(e.from_key)
            rev_deps[e.from_key].add(e.to_key)

        for key, state in states.items():
            if not deps[key]:
                state.status = NodeStatus.READY

        t0 = time.perf_counter()
        iteration = 0

        async def execute_one(key: str) -> None:
            state = states[key]
            spec = state.spec
            async with self._sem:
                state.status = NodeStatus.RUNNING
                state.attempt_count += 1
                state.started_at = datetime.now(timezone.utc)
                t_node = time.perf_counter()
                try:
                    inputs = {
                        dep: states[dep].output
                        for dep in deps[key]
                        if states[dep].status == NodeStatus.SUCCEEDED
                    }
                    ctx = {**context, "inputs": inputs, "query": query, "run_id": run_id}
                    out = await spec.handler(ctx)
                    state.output = out
                    state.status = NodeStatus.SUCCEEDED
                except Exception as exc:
                    state.error = str(exc)
                    if state.attempt_count <= spec.max_retries:
                        state.status = NodeStatus.RETRYING
                    else:
                        state.status = NodeStatus.FAILED
                    logger.exception("Node %s failed", key)
                finally:
                    state.ended_at = datetime.now(timezone.utc)
                    state.duration_ms = (time.perf_counter() - t_node) * 1000

        while True:
            iteration += 1
            ready = [
                k
                for k, s in states.items()
                if s.status in (NodeStatus.READY, NodeStatus.RETRYING)
            ]
            if not ready:
                pending = any(
                    s.status in (NodeStatus.PENDING, NodeStatus.RUNNING) for s in states.values()
                )
                if not pending:
                    break
                await asyncio.sleep(0.01)
                continue

            for k in ready:
                if states[k].status == NodeStatus.RETRYING:
                    states[k].status = NodeStatus.READY

            await asyncio.gather(*(execute_one(k) for k in ready))

            for key, state in states.items():
                if state.status != NodeStatus.PENDING:
                    continue
                if all(states[d].status == NodeStatus.SUCCEEDED for d in deps[key]):
                    state.status = NodeStatus.READY
                elif any(states[d].status == NodeStatus.FAILED for d in deps[key]):
                    state.status = NodeStatus.SKIPPED

        wall_ms = (time.perf_counter() - t0) * 1000
        terminal = [s for s in states.values() if s.status == NodeStatus.FAILED]
        status = "failed" if terminal else "succeeded"
        final = None
        if "formatter" in states and states["formatter"].status == NodeStatus.SUCCEEDED:
            final = states["formatter"].output.get("answer")
        elif "answer" in states and states["answer"].status == NodeStatus.SUCCEEDED:
            final = states["answer"].output.get("answer")

        return DagRunResult(
            run_id=run_id,
            query=query,
            status=status,
            nodes=list(states.values()),
            final_answer=final,
            wall_clock_ms=wall_ms,
            iteration_count=iteration,
            metadata={"parallel_layers": self._parallel_layers(states, rev_deps)},
        )

    @staticmethod
    def _parallel_layers(
        states: dict[str, NodeState], rev_deps: dict[str, set[str]]
    ) -> list[dict[str, Any]]:
        """Summarize concurrent layers for benchmark proof."""
        by_lane: dict[int, list[dict[str, Any]]] = {}
        for key, state in states.items():
            lane = state.spec.lane
            by_lane.setdefault(lane, []).append(
                {
                    "key": key,
                    "duration_ms": state.duration_ms,
                    "status": state.status.value,
                }
            )
        layers = []
        for lane, nodes in sorted(by_lane.items()):
            durations = [n["duration_ms"] or 0 for n in nodes if n["status"] == "succeeded"]
            layers.append(
                {
                    "lane": lane,
                    "nodes": nodes,
                    "max_ms": max(durations) if durations else 0,
                    "sum_ms": sum(durations),
                }
            )
        return layers
