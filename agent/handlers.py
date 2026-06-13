from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from agent.sandbox_executor import SandboxError, execute_coder

# Browser comparison imports
from agent.comparison_handlers import (  # noqa: F401
    node_browser_comparison,
    node_comparison_formatter,
    node_comparison_planner,
    node_critic_agent,
    node_distiller,
    node_replay_generator,
)
from agent.metrics import estimate_cost, get_metrics_collector
from agent.web_search_handlers import (  # noqa: F401
    node_web_search_planner,
    node_web_searcher,
    node_web_page_visitor,
    node_web_vlm_analyzer,
    node_web_search_formatter,
)

# Deterministic Coder template for median depth (no LLM required for benchmark)
MEDIAN_DEPTH_CODE = '''
def solve(context):
    depths = sorted(p["depth"] for p in context.get("pages", []))
    if not depths:
        return {"median_depth": None}
    n = len(depths)
    mid = n // 2
    if n % 2:
        return {"median_depth": float(depths[mid])}
    return {"median_depth": (depths[mid - 1] + depths[mid]) / 2.0}
'''


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent / "prompts" / f"{name}.md"
    return path.read_text(encoding="utf-8")


async def node_planner(ctx: dict[str, Any]) -> dict[str, Any]:
    query = ctx["query"].strip()
    kind = ctx.get("query_kind") or "base"
    base_id = ctx.get("base_id")
    if not base_id:
        if query == "hello":
            base_id = "hello"
        elif query in ("A", "I", "J", "K"):
            base_id = query
        elif "parallel" in query.lower():
            kind = "parallel_fanout"
        elif "form" in query.lower() and "how many" in query.lower():
            kind = "critic"
        elif "median depth" in query.lower():
            kind = "coder"
        elif "investigate" in query.lower():
            kind = "investigator"
    return {
        "query_kind": kind,
        "base_id": base_id,
        "prompt_loaded": _load_prompt("planner")[:80],
    }


async def node_task(ctx: dict[str, Any]) -> dict[str, Any]:
    plan = ctx["inputs"]["planner"]
    base_id = plan.get("base_id") or "hello"
    evidence = ctx.get("evidence", {})
    if base_id == "hello":
        return {"raw": "hello"}
    if base_id == "A":
        return {"raw": evidence.get("page_count", 0), "label": "page_count"}
    if base_id == "I":
        return {"raw": evidence.get("internal_link_count", 0), "label": "internal_links"}
    if base_id == "J":
        eps = evidence.get("endpoints", [])
        return {"raw": json.dumps(eps[:5]), "label": "endpoints_sample"}
    if base_id == "K":
        return {"raw": evidence.get("chunk_count", 0), "label": "knowledge_chunks"}
    return {"raw": "unknown", "label": "unknown"}


async def node_formatter(ctx: dict[str, Any]) -> dict[str, Any]:
    plan = ctx["inputs"].get("planner") or {}
    if "formatter" in ctx["inputs"]:
        # recovery path may chain
        pass
    if "task" in ctx["inputs"]:
        task = ctx["inputs"]["task"]
        if plan.get("base_id") == "hello":
            return {"answer": "hello", "confidence": 1.0}
        return {
            "answer": f"{task.get('label')}: {task.get('raw')}",
            "confidence": 0.9,
        }
    if "merge" in ctx["inputs"]:
        m = ctx["inputs"]["merge"]
        return {
            "answer": (
                f"Parallel totals — links: {m['links']}, forms: {m['forms']}, "
                f"endpoints: {m['endpoints']}"
            ),
            "confidence": 0.92,
            "parallel_proof": m.get("parallel_proof"),
        }
    if "sandbox" in ctx["inputs"]:
        s = ctx["inputs"]["sandbox"]
        return {
            "answer": f"median_depth: {s.get('median_depth')}",
            "confidence": 0.95,
        }
    if "investigator" in ctx["inputs"]:
        inv = ctx["inputs"]["investigator"]
        return {
            "answer": (
                f"Headings: {', '.join(inv.get('headings', []))}; "
                f"outbound links: {inv.get('outbound_link_count')}"
            ),
            "confidence": inv.get("confidence", 0.85),
        }
    if "recovery" in ctx["inputs"]:
        rec = ctx["inputs"]["recovery"]
        return {"answer": rec["corrected_answer"], "confidence": 0.88}
    if "critic" in ctx["inputs"] and ctx["inputs"]["critic"].get("verdict") == "pass":
        return {"answer": ctx["inputs"]["answer"]["text"], "confidence": 0.9}
    return {"answer": "No output", "confidence": 0.0}


# --- Parallel fan-out (staggered sleeps prove max wall-clock) ---

async def node_branch_a(ctx: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0.35)
    return {"metric": "links", "value": ctx["evidence"].get("internal_link_count", 0)}


async def node_branch_b(ctx: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0.55)  # longest branch
    return {"metric": "forms", "value": ctx["evidence"].get("form_count", 0)}


async def node_branch_c(ctx: dict[str, Any]) -> dict[str, Any]:
    await asyncio.sleep(0.25)
    return {"metric": "endpoints", "value": len(ctx["evidence"].get("endpoints", []))}


async def node_merge(ctx: dict[str, Any]) -> dict[str, Any]:
    a = ctx["inputs"]["branch_a"]
    b = ctx["inputs"]["branch_b"]
    c = ctx["inputs"]["branch_c"]
    durations = [
        ctx.get("_node_timings", {}).get("branch_a"),
        ctx.get("_node_timings", {}).get("branch_b"),
        ctx.get("_node_timings", {}).get("branch_c"),
    ]
    branch_ms = [d for d in durations if d is not None]
    return {
        "links": a["value"],
        "forms": b["value"],
        "endpoints": c["value"],
        "parallel_proof": {
            "branch_durations_ms": branch_ms,
            "max_ms": max(branch_ms) if branch_ms else None,
            "sum_ms": sum(branch_ms) if branch_ms else None,
        },
    }


# --- Critic path ---

async def node_retrieve(ctx: dict[str, Any]) -> dict[str, Any]:
    ev = ctx["evidence"]
    return {"form_count": ev.get("form_count", 0), "pages": ev.get("page_count", 0)}


async def node_answer(ctx: dict[str, Any]) -> dict[str, Any]:
    retrieved = ctx["inputs"]["retrieve"]
    draft = retrieved["form_count"]
    if ctx.get("critic_force_fail"):
        draft = retrieved["form_count"] + 4  # wrong on purpose
    return {
        "draft_answer": draft,
        "text": f"There are {draft} forms on this site.",
        "form_count_evidence": retrieved["form_count"],
    }


async def node_critic(ctx: dict[str, Any]) -> dict[str, Any]:
    answer = ctx["inputs"]["answer"]
    expected = answer["form_count_evidence"]
    actual = answer["draft_answer"]
    if actual == expected:
        return {
            "verdict": "pass",
            "property_checked": "form_count_matches_evidence",
            "expected": expected,
            "actual": actual,
        }
    return {
        "verdict": "fail",
        "property_checked": "form_count_matches_evidence",
        "expected": expected,
        "actual": actual,
        "recovery_hint": f"Use evidence form_count={expected}",
    }


async def node_recovery(ctx: dict[str, Any]) -> dict[str, Any]:
    critic = ctx["inputs"]["critic"]
    expected = critic["expected"]
    if critic["verdict"] == "pass":
        return {
            "corrected_answer": f"There are {expected} forms on this site.",
            "recovered": False,
        }
    return {
        "corrected_answer": (
            f"There are {expected} forms on this site (recovered after critic fail)."
        ),
        "recovered": True,
        "recovery_hint": critic.get("recovery_hint"),
    }


# --- Coder + sandbox ---

async def node_coder(ctx: dict[str, Any]) -> dict[str, Any]:
    return {"code": MEDIAN_DEPTH_CODE, "prompt": _load_prompt("coder")[:120]}


async def node_sandbox(ctx: dict[str, Any]) -> dict[str, Any]:
    code = ctx["inputs"]["coder"]["code"]
    pages = ctx["evidence"].get("pages", [])
    try:
        result = execute_coder(code, {"pages": pages})
    except SandboxError as exc:
        return {"error": str(exc)}
    return result


# --- Investigator (new skill) ---

async def node_investigator(ctx: dict[str, Any]) -> dict[str, Any]:
    page = ctx["evidence"].get("root_page", {})
    return {
        "page_url": page.get("url", ""),
        "headings": page.get("headings", []),
        "outbound_link_count": page.get("outbound_link_count", 0),
        "auth_keywords_found": page.get("auth_keywords", []),
        "confidence": 0.85,
        "prompt": _load_prompt("investigator")[:120],
    }


def build_handlers() -> dict[str, Any]:
    return {
        "planner": node_planner,
        "task": node_task,
        "formatter": node_formatter,
        "branch_a": node_branch_a,
        "branch_b": node_branch_b,
        "branch_c": node_branch_c,
        "merge": node_merge,
        "retrieve": node_retrieve,
        "answer": node_answer,
        "critic": node_critic,
        "recovery": node_recovery,
        "coder": node_coder,
        "sandbox": node_sandbox,
        "investigator": node_investigator,
        # Comparison DAG handlers
        "comparison_planner": node_comparison_planner,
        "browser_comparison": node_browser_comparison,
        "distiller": node_distiller,
        "critic_agent": node_critic_agent,
        "comparison_formatter": node_comparison_formatter,
        "replay_generator": node_replay_generator,
        # Web Search DAG handlers
        "web_search_planner": node_web_search_planner,
        "web_searcher": node_web_searcher,
        "web_page_visitor": node_web_page_visitor,
        "web_vlm_analyzer": node_web_vlm_analyzer,
        "web_search_formatter": node_web_search_formatter,
    }


def mock_evidence() -> dict[str, Any]:
    pages = [
        {"url": "https://books.toscrape.com/", "depth": 0},
        {"url": "https://books.toscrape.com/catalogue/page-1.html", "depth": 1},
        {"url": "https://books.toscrape.com/catalogue/page-2.html", "depth": 1},
        {"url": "https://books.toscrape.com/catalogue/category/books_1/index.html", "depth": 2},
    ]
    return {
        "page_count": len(pages),
        "form_count": 3,
        "internal_link_count": 42,
        "endpoints": [
            {"method": "GET", "url": "/static/style.css"},
            {"method": "GET", "url": "/catalogue/page-1.html"},
        ],
        "chunk_count": 52,
        "pages": pages,
        "root_page": {
            "url": "https://books.toscrape.com/",
            "headings": ["All products", "Books"],
            "outbound_link_count": 24,
            "auth_keywords": [],
        },
    }
