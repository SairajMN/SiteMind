"""Metrics — track success rates, costs, latency, and execution statistics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionMetrics:
    """Tracks metrics across comparison executions."""

    query: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    wall_clock_ms: float = 0.0
    browser_duration_ms: float = 0.0
    distiller_duration_ms: float = 0.0
    critic_duration_ms: float = 0.0
    planner_duration_ms: float = 0.0
    formatter_duration_ms: float = 0.0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    extraction_success: bool = False
    critic_pass: bool = False
    recovery_attempts: int = 0
    recovery_success: bool = False
    browser_actions: int = 0
    items_extracted: int = 0
    path_selected: str = ""
    final_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "wall_clock_ms": round(self.wall_clock_ms, 2),
            "browser_duration_ms": round(self.browser_duration_ms, 2),
            "distiller_duration_ms": round(self.distiller_duration_ms, 2),
            "critic_duration_ms": round(self.critic_duration_ms, 2),
            "planner_duration_ms": round(self.planner_duration_ms, 2),
            "formatter_duration_ms": round(self.formatter_duration_ms, 2),
            "total_tokens": self.total_tokens,
            "estimated_cost": round(self.estimated_cost, 4),
            "extraction_success": self.extraction_success,
            "critic_pass": self.critic_pass,
            "recovery_attempts": self.recovery_attempts,
            "recovery_success": self.recovery_success,
            "browser_actions": self.browser_actions,
            "items_extracted": self.items_extracted,
            "path_selected": self.path_selected,
            "final_status": self.final_status,
        }


class MetricsCollector:
    """Collects and aggregates execution metrics."""

    def __init__(self) -> None:
        self.runs: list[ExecutionMetrics] = []
        self._current: ExecutionMetrics | None = None

    def start_run(self, query: str) -> ExecutionMetrics:
        self._current = ExecutionMetrics(
            query=query,
            start_time=time.perf_counter(),
        )
        return self._current

    def end_run(self) -> ExecutionMetrics:
        if self._current:
            self._current.end_time = time.perf_counter()
            self._current.wall_clock_ms = (
                self._current.end_time - self._current.start_time
            ) * 1000
            self.runs.append(self._current)
        return self._current or ExecutionMetrics()

    def get_summary(self) -> dict[str, Any]:
        if not self.runs:
            return {"message": "No runs recorded"}

        total = len(self.runs)
        successes = sum(1 for r in self.runs if r.final_status == "PASSED")

        return {
            "total_runs": total,
            "successful_runs": successes,
            "extraction_success_rate": (
                sum(1 for r in self.runs if r.extraction_success) / total * 100
            ),
            "critic_pass_rate": sum(1 for r in self.runs if r.critic_pass) / total * 100,
            "recovery_rate": (
                sum(1 for r in self.runs if r.recovery_success) / total * 100
                if any(r.recovery_attempts > 0 for r in self.runs)
                else 0
            ),
            "avg_wall_clock_ms": sum(r.wall_clock_ms for r in self.runs) / total,
            "avg_browser_actions": sum(r.browser_actions for r in self.runs) / total,
            "avg_items_extracted": sum(r.items_extracted for r in self.runs) / total,
            "avg_estimated_cost": sum(r.estimated_cost for r in self.runs) / total,
        }


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _metrics_collector


def estimate_cost(duration_ms: float, actions: int, tokens: int = 0) -> float:
    """Estimate execution cost based on browser actions and duration."""
    # Estimated costs
    browser_cost_per_minute = 0.01  # $0.01 per minute for browser
    action_cost = 0.001  # $0.001 per browser action
    token_cost = tokens * 0.000002  # $2 per million tokens

    browser_time_minutes = duration_ms / 60000
    cost = (
        browser_time_minutes * browser_cost_per_minute
        + actions * action_cost
        + token_cost
    )
    return cost
