from __future__ import annotations

from typing import Any

from app.dag.models import EdgeSpec, NodeSpec


def plan_site_crawl_dag(handlers: dict[str, Any]) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    """Site analysis DAG: crawl -> parallel extractors -> workflow -> knowledge -> eval."""
    nodes = [
        NodeSpec("planner", "planner", handlers["planner"], lane=0),
        NodeSpec("crawl", "crawl", handlers["crawl"], lane=1),
        NodeSpec("dom", "extractor", handlers["dom"], lane=2),
        NodeSpec("form", "extractor", handlers["form"], lane=2),
        NodeSpec("endpoint", "extractor", handlers["endpoint"], lane=2),
        NodeSpec("auth", "extractor", handlers["auth"], lane=2),
        NodeSpec("screenshot", "extractor", handlers["screenshot"], lane=2),
        NodeSpec("network_trace", "extractor", handlers["network_trace"], lane=2),
        NodeSpec("workflow_miner", "workflow", handlers["workflow_miner"], lane=3),
        NodeSpec("knowledge_builder", "knowledge", handlers["knowledge_builder"], lane=4),
        NodeSpec("api_generator", "api", handlers["api_generator"], lane=4),
        NodeSpec("evaluation", "evaluation", handlers["evaluation"], lane=5),
    ]
    edges = [
        EdgeSpec("planner", "crawl"),
        EdgeSpec("crawl", "dom"),
        EdgeSpec("crawl", "form"),
        EdgeSpec("crawl", "endpoint"),
        EdgeSpec("crawl", "auth"),
        EdgeSpec("crawl", "screenshot"),
        EdgeSpec("crawl", "network_trace"),
        EdgeSpec("dom", "workflow_miner"),
        EdgeSpec("form", "workflow_miner"),
        EdgeSpec("endpoint", "workflow_miner"),
        EdgeSpec("auth", "workflow_miner"),
        EdgeSpec("screenshot", "workflow_miner"),
        EdgeSpec("dom", "knowledge_builder"),
        EdgeSpec("form", "knowledge_builder"),
        EdgeSpec("endpoint", "knowledge_builder"),
        EdgeSpec("auth", "knowledge_builder"),
        EdgeSpec("screenshot", "knowledge_builder"),
        EdgeSpec("workflow_miner", "knowledge_builder"),
        EdgeSpec("workflow_miner", "api_generator"),
        EdgeSpec("crawl", "evaluation"),
        EdgeSpec("knowledge_builder", "evaluation"),
        EdgeSpec("api_generator", "evaluation"),
    ]
    return nodes, edges


def plan_agent_query_dag(
    handlers: dict[str, Any], query_kind: str
) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    """Planner for assignment / agent queries."""
    if query_kind == "parallel_fanout":
        nodes = [
            NodeSpec("planner", "planner", handlers["planner"], lane=0),
            NodeSpec("branch_a", "branch", handlers["branch_a"], lane=1),
            NodeSpec("branch_b", "branch", handlers["branch_b"], lane=1),
            NodeSpec("branch_c", "branch", handlers["branch_c"], lane=1),
            NodeSpec("merge", "merge", handlers["merge"], lane=2),
            NodeSpec("formatter", "formatter", handlers["formatter"], lane=3),
        ]
        edges = [
            EdgeSpec("planner", "branch_a"),
            EdgeSpec("planner", "branch_b"),
            EdgeSpec("planner", "branch_c"),
            EdgeSpec("branch_a", "merge"),
            EdgeSpec("branch_b", "merge"),
            EdgeSpec("branch_c", "merge"),
            EdgeSpec("merge", "formatter"),
        ]
        return nodes, edges

    if query_kind == "critic":
        nodes = [
            NodeSpec("planner", "planner", handlers["planner"], lane=0),
            NodeSpec("retrieve", "retrieve", handlers["retrieve"], lane=1),
            NodeSpec("answer", "answer", handlers["answer"], lane=2),
            NodeSpec("critic", "critic", handlers["critic"], lane=3),
            NodeSpec("recovery", "recovery", handlers["recovery"], lane=4),
            NodeSpec("formatter", "formatter", handlers["formatter"], lane=5),
        ]
        edges = [
            EdgeSpec("planner", "retrieve"),
            EdgeSpec("retrieve", "answer"),
            EdgeSpec("answer", "critic"),
            EdgeSpec("critic", "recovery"),
            EdgeSpec("recovery", "formatter"),
        ]
        return nodes, edges

    if query_kind == "coder":
        nodes = [
            NodeSpec("planner", "planner", handlers["planner"], lane=0),
            NodeSpec("coder", "coder", handlers["coder"], lane=1),
            NodeSpec("sandbox", "sandbox", handlers["sandbox"], lane=2),
            NodeSpec("formatter", "formatter", handlers["formatter"], lane=3),
        ]
        edges = [
            EdgeSpec("planner", "coder"),
            EdgeSpec("coder", "sandbox"),
            EdgeSpec("sandbox", "formatter"),
        ]
        return nodes, edges

    if query_kind == "investigator":
        nodes = [
            NodeSpec("planner", "planner", handlers["planner"], lane=0),
            NodeSpec("investigator", "investigator", handlers["investigator"], lane=1),
            NodeSpec("formatter", "formatter", handlers["formatter"], lane=2),
        ]
        edges = [
            EdgeSpec("planner", "investigator"),
            EdgeSpec("investigator", "formatter"),
        ]
        return nodes, edges

    # base queries: planner -> task -> formatter
    nodes = [
        NodeSpec("planner", "planner", handlers["planner"], lane=0),
        NodeSpec("task", "task", handlers["task"], lane=1),
        NodeSpec("formatter", "formatter", handlers["formatter"], lane=2),
    ]
    edges = [
        EdgeSpec("planner", "task"),
        EdgeSpec("task", "formatter"),
    ]
    return nodes, edges
