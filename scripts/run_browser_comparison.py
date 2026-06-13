#!/usr/bin/env python3
"""Run the browser comparison system — demonstrates real browser intelligence."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent.orchestrator import run_query, format_run_log
from agent.metrics import get_metrics_collector


def print_header(text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


async def run_comparison_demo() -> None:
    """Run the full browser comparison pipeline."""
    print_header("BROWSER COMPARISON INTELLIGENCE SYSTEM")
    print("A production-grade browser research platform")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Test 1: HuggingFace model comparison
    query = "Compare top 3 Hugging Face text-generation models sorted by likes"
    print_header(f"TEST 1: {query}")

    try:
        result = await run_query(query)

        print("\n=== EXECUTION RESULT ===")
        print(f"Status: {result.status}")
        print(f"Iterations: {result.iteration_count}")
        print(f"Wall Clock: {result.wall_clock_ms:.2f} ms")
        print(f"Final Answer (first 500 chars):")
        if result.final_answer:
            print(result.final_answer[:500])
        else:
            print("(no answer produced)")

        # Show node states
        print("\n=== NODE STATES ===")
        for ns in result.nodes:
            status_icon = "✓" if ns.status.value == "succeeded" else "✗" if ns.status.value == "failed" else "~"
            output_snippet = ""
            if ns.output:
                if "answer" in ns.output:
                    output_snippet = f" answer={ns.output['answer'][:100]}..."
                elif "items_count" in ns.output:
                    output_snippet = f" items={ns.output.get('items_count')}"
                elif "critic_status" in ns.output:
                    output_snippet = f" critic={ns.output.get('critic_status')}"
                elif "replay_filepath" in ns.output:
                    output_snippet = f" replay={ns.output.get('replay_filepath')}"
                elif "total_extracted" in ns.output:
                    output_snippet = f" extracted={ns.output.get('total_extracted')}"
            print(f"  {status_icon} {ns.spec.key:25s} {ns.status.value:12s} {ns.duration_ms or 0:8.0f}ms{output_snippet}")

        return result

    except Exception as exc:
        print(f"\nERROR: {exc}")
        import traceback
        traceback.print_exc()
        return None


async def run_comparison_only() -> None:
    """Run just the browser comparison handler directly for debugging."""
    print_header("BROWSER ENGINE DIRECT TEST")

    from agent.browser.browser_engine import create_browser_engine

    engine = await create_browser_engine()
    try:
        url = "https://huggingface.co/models"
        print(f"Navigating to {url}...")
        result = await engine.extract_content(url)
        print(f"Path: {result.get('path', 'unknown')}")
        print(f"Success: {result.get('success', False)}")
        print(f"Title: {result.get('title', 'N/A')}")

        if result.get("success"):
            print(f"Content length: {len(result.get('content', ''))}")
            print(f"Items found: {len(result.get('items', []))}")
            items = result.get("items", [])
            for i, item in enumerate(items[:5]):
                print(f"  {i+1}. {item.get('name')} - {item.get('likes', 'N/A')}")

        # Try sort action
        print("\nClicking sort by Likes...")
        sort_result = await engine.click_sort("Likes")
        print(f"Sort result: {sort_result.get('success', False)}")

        # Get final page content
        if engine._page:
            print(f"\nFinal URL: {engine._page.url}")
            print(f"Final Title: {await engine._page.title()}")

        report = engine.get_report_data()
        print(f"\nActions logged: {report.get('action_count', 0)}")

        if engine.screenshot_mgr:
            screenshots = engine.screenshot_mgr.get_report_data()
            print(f"Screenshots captured: {len(screenshots)}")
            for s in screenshots:
                print(f"  - {s.get('filename')}: {s.get('label')} ({s.get('kind')})")

    except Exception as exc:
        print(f"ERROR: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.cleanup()


async def main() -> None:
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Browser Comparison Intelligence System")
    parser.add_argument("--mode", choices=["full", "browser", "compare"], default="full",
                        help="Execution mode")
    parser.add_argument("--query", type=str, default=None,
                        help="Custom query for comparison")
    args = parser.parse_args()

    if args.mode == "browser":
        await run_comparison_only()
    elif args.mode == "compare":
        query = args.query or "Compare top 3 Hugging Face text-generation models sorted by likes"
        result = await run_query(query)
        if result:
            print("\n" + format_run_log(result))
    else:
        await run_comparison_demo()

    # Show metrics summary
    metrics = get_metrics_collector()
    summary = metrics.get_summary()
    if summary.get("total_runs", 0) > 0:
        print("\n=== METRICS SUMMARY ===")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
