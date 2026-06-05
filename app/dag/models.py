from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine


class NodeStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class NodeSpec:
    key: str
    node_type: str
    handler: Callable[..., Coroutine[Any, Any, dict[str, Any]]]
    lane: int = 0
    max_retries: int = 1


@dataclass
class EdgeSpec:
    from_key: str
    to_key: str
    edge_type: str = "depends_on"


@dataclass
class NodeState:
    spec: NodeSpec
    status: NodeStatus = NodeStatus.PENDING
    attempt_count: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_ms: float | None = None
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class DagRunResult:
    run_id: str
    query: str
    status: str
    nodes: list[NodeState]
    final_answer: str | None = None
    wall_clock_ms: float = 0.0
    iteration_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
