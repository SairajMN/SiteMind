#!/usr/bin/env python3
"""Run DAG agent assignment proofs; writes logs to logs/assignment/."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.orchestrator import format_run_log, load_config, run_query

LOG_DIR = ROOT / "logs" / "assignment"


def _write(name: str, content: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / name
    path.write_text(content, encoding="utf-8")
    return path


async def run_base_queries() -> list[dict]:
    config = load_config()
    results = []
    for item in config["base_queries"]:
        r = await run_query(
            item["query"],
            max_iterations=item["max_iterations"],
            max_wall_clock_sec=item["max_wall_clock_sec"],
        )
        ok = r.metadata.get("bounds", {})
        passed = ok.get("iterations_ok") and ok.get("wall_clock_ok") and r.status == "succeeded"
        log = format_run_log(r)
        _write(f"1_base_{item['id']}.log", log)
        results.append(
            {
                "id": item["id"],
                "query": item["query"],
                "passed": passed,
                "wall_clock_ms": r.wall_clock_ms,
                "iterations": r.iteration_count,
            }
        )
    return results


async def run_parallel_fanout() -> dict:
    config = load_config()
    q = config["assignment_queries"]["parallel_fanout"]["query"]
    r = await run_query(q)
    layers = r.metadata.get("parallel_layers", [])
    lane1 = next((L for L in layers if L.get("lane") == 1), {})
    max_ms = lane1.get("max_ms", 0)
    sum_ms = lane1.get("sum_ms", 0)
    parallel_ok = max_ms > 0 and sum_ms > max_ms * 1.2  # max << sum proves concurrency
    log = format_run_log(r) + f"\n\nPARALLEL_PROOF max_ms={max_ms} sum_ms={sum_ms} ok={parallel_ok}"
    _write("2_parallel_fanout.log", log)
    return {"parallel_ok": parallel_ok, "max_ms": max_ms, "sum_ms": sum_ms, "layers": layers}


async def run_critic_demo() -> dict:
    config = load_config()
    q = config["assignment_queries"]["critic_demo"]["query"]

    pass_run = await run_query(q, critic_force_fail=False)
    _write("3_critic_pass.log", format_run_log(pass_run))

    fail_run = await run_query(q, critic_force_fail=True)
    recovery = next((n for n in fail_run.nodes if n.spec.key == "recovery"), None)
    critic = next((n for n in fail_run.nodes if n.spec.key == "critic"), None)
    recovered = recovery and recovery.output.get("recovered") is True
    critic_failed = critic and critic.output.get("verdict") == "fail"
    log = format_run_log(fail_run) + f"\n\ncritic_fail={critic_failed} recovery={recovered}"
    _write("3_critic_fail_recovery.log", log)

    return {
        "pass_run_ok": pass_run.status == "succeeded",
        "critic_fail": critic_failed,
        "recovery_spliced": recovered,
    }


async def run_coder_demo() -> dict:
    config = load_config()
    q = config["assignment_queries"]["coder_demo"]["query"]
    r = await run_query(q)
    sandbox = next((n for n in r.nodes if n.spec.key == "sandbox"), None)
    median = sandbox.output.get("median_depth") if sandbox else None
    _write("4_coder_sandbox.log", format_run_log(r))
    return {"median_depth": median, "ok": median is not None}


async def run_investigator_demo() -> dict:
    config = load_config()
    q = config["assignment_queries"]["investigator_demo"]["query"]
    r = await run_query(q)
    inv = next((n for n in r.nodes if n.spec.key == "investigator"), None)
    _write("5_investigator_skill.log", format_run_log(r))
    return {
        "ok": inv is not None and inv.status.value == "succeeded",
        "headings": inv.output.get("headings") if inv else None,
    }


async def _run_all() -> None:
    ts = datetime.now(timezone.utc).isoformat()
    summary = {"timestamp": ts, "parts": {}}

    summary["parts"]["1_base_queries"] = await run_base_queries()
    summary["parts"]["2_parallel"] = await run_parallel_fanout()
    summary["parts"]["3_critic"] = await run_critic_demo()
    summary["parts"]["4_coder"] = await run_coder_demo()
    summary["parts"]["5_investigator"] = await run_investigator_demo()

    all_base = all(x["passed"] for x in summary["parts"]["1_base_queries"])
    summary["all_passed"] = (
        all_base
        and summary["parts"]["2_parallel"]["parallel_ok"]
        and summary["parts"]["3_critic"]["pass_run_ok"]
        and summary["parts"]["3_critic"]["critic_fail"]
        and summary["parts"]["3_critic"]["recovery_spliced"]
        and summary["parts"]["4_coder"]["ok"]
        and summary["parts"]["5_investigator"]["ok"]
    )

    _write("SUMMARY.json", json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"\nLogs written to {LOG_DIR}")
    sys.exit(0 if summary["all_passed"] else 1)


def main() -> None:
    asyncio.run(_run_all())


if __name__ == "__main__":
    main()
