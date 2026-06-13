"""Comparison DAG node handlers for the browser comparison system."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agent.browser.browser_engine import create_browser_engine
from agent.critic_agent import evaluate_comparison
from agent.distiller import distill_content
from agent.metrics import get_metrics_collector
from agent.replay_generator import generate_replay_report
from agent.skills.skill_catalog import (
    get_comparison_dimensions,
    get_ranking_criteria,
    identify_site_from_query,
    select_best_skill,
)

logger = logging.getLogger(__name__)


def _load_prompt(name: str) -> str:
    path = Path(__file__).parent / "prompts" / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


async def node_comparison_planner(ctx: dict[str, Any]) -> dict[str, Any]:
    """Browser comparison planner — determines target URL, actions, and dimensions."""
    query = ctx["query"].strip()
    target_url = identify_site_from_query(query) or "https://huggingface.co/models"
    skill, confidence = select_best_skill(query, target_url)
    dimensions = get_comparison_dimensions(query)
    ranking = get_ranking_criteria(query)

    # Build intelligent URL with query params for HuggingFace
    query_lower = query.lower()
    if "huggingface" in query_lower or "hugging face" in query_lower:
        if "text-generation" in query_lower or "text generation" in query_lower:
            if ranking == "likes":
                target_url = "https://huggingface.co/models?pipeline_tag=text-generation&sort=likes"
            elif ranking == "downloads":
                target_url = "https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads"
            else:
                target_url = "https://huggingface.co/models?pipeline_tag=text-generation&sort=likes"
        else:
            target_url = "https://huggingface.co/models?sort=likes"

    plan = {
        "target_url": target_url,
        "task_type": skill.comparison_types[0] if skill.comparison_types else "ai_models",
        "comparison_dimensions": dimensions,
        "ranking_criteria": ranking,
        "skill_name": skill.skill_name,
        "min_items": 3,
        "actions_required": ["search", "click", "sort"],
        "confidence": confidence,
        "prompt_loaded": _load_prompt("comparison_planner")[:80],
    }

    logger.info("Comparison planner: target=%s dimensions=%s ranking=%s", target_url, dimensions, ranking)
    return plan


async def node_browser_comparison(ctx: dict[str, Any]) -> dict[str, Any]:
    """Execute browser comparison using the multi-path engine."""
    plan = ctx["inputs"]["planner"]
    query = ctx["query"]
    target_url = plan.get("target_url", "https://huggingface.co/models")
    ranking = plan.get("ranking_criteria", "likes")
    task_type = plan.get("task_type", "ai_models")

    metrics = get_metrics_collector()
    metrics.start_run(query)

    engine = await create_browser_engine()
    try:
        logger.info("Browser comparison: navigating to %s", target_url)

        # Action 1: Navigate to target
        nav_result = await engine.extract_content(target_url)

        # Always perform at least 3 visible browser actions
        if engine._page:
            # Action 2: Try sort by ranking criterion
            sort_keywords = {"likes": "Likes", "downloads": "Downloads", "popular": "Popular"}
            sort_text = sort_keywords.get(ranking, "Likes")
            sort_result = await engine.click_sort(sort_text)

            # Action 3: Scroll the page to load more content
            try:
                await engine.action_logger.log_action("scroll", target="page_down", url=engine._page.url)
                await engine._page.evaluate("window.scrollBy(0, 500)")
                await engine._page.wait_for_timeout(1000)
                await engine.action_logger.log_action("scroll_complete", target="page_down", url=engine._page.url, status="success")
            except Exception:
                pass

            # Action 4: Extract content after scrolling (if initial extract had limited data)
            if engine.selected_path and "deterministic" in str(engine.selected_path):
                search_terms = []
                if "text-generation" in query.lower() or "text generation" in query.lower():
                    search_terms.append("text-generation")
                if "model" in query.lower():
                    search_terms.append("models")
                if search_terms:
                    await engine.search(search_terms[0])

                # Re-extract to get fresh content after interactions
                updated = await engine.extract_content(engine._page.url)
                if updated.get("content"):
                    nav_result = updated

        report_data = engine.get_report_data()
        result = {
            "path": engine.selected_path.value if engine.selected_path else "unknown",
            "url": target_url,
            "report_data": report_data,
            "success": True,
            "content": nav_result.get("content", ""),
            "items": nav_result.get("items", []),
            "tables": nav_result.get("tables", []),
            "listings": nav_result.get("listings", []),
            "title": nav_result.get("title", ""),
            "action_count": engine.action_logger.get_action_count(),
        }

        metrics.end_run()
        return result

    except Exception as exc:
        logger.exception("Browser comparison failed: %s", exc)
        metrics.end_run()
        return {
            "path": "failed",
            "url": target_url,
            "report_data": engine.get_report_data(),
            "success": False,
            "content": "",
            "items": [],
            "title": "",
            "error": str(exc),
        }
    finally:
        await engine.cleanup()


async def node_distiller(ctx: dict[str, Any]) -> dict[str, Any]:
    """Distill browser output into structured comparison items."""
    browser_output = ctx["inputs"]["browser_comparison"]
    query = ctx["query"]
    plan = ctx["inputs"].get("planner", {})

    result = await distill_content(
        browser_output,
        query=query,
        url=browser_output.get("url", ""),
        min_items=plan.get("min_items", 3),
    )

    metrics = get_metrics_collector()
    if metrics._current:
        metrics._current.items_extracted = result.get("total_extracted", 0)

    logger.info("Distiller: extracted %d items with confidence %.2f",
                 result.get("total_extracted", 0), result.get("confidence", 0))
    return result


async def node_critic_agent(ctx: dict[str, Any]) -> dict[str, Any]:
    """Run critic evaluation on comparison output."""
    distiller_output = ctx["inputs"]["distiller"]
    browser_output = ctx["inputs"]["browser_comparison"]
    query = ctx["query"]

    browser_report = browser_output.get("report_data", {})
    browser_actions = browser_report.get("actions", [])

    result = await evaluate_comparison(
        distiller_output,
        browser_actions,
        browser_report,
        query=query,
        min_items=3,
        min_actions=3,
    )

    metrics = get_metrics_collector()
    if metrics._current:
        metrics._current.critic_pass = result.get("status") == "PASSED"
        metrics._current.extraction_success = distiller_output.get("total_extracted", 0) >= 3
        metrics._current.browser_actions = len(browser_actions)

    logger.info("Critic agent: %s (%d/%d checks passed)",
                 result.get("status"), result.get("passed_count"), result.get("total_checks"))
    return result


async def node_comparison_formatter(ctx: dict[str, Any]) -> dict[str, Any]:
    """Format comparison output into final answer with table."""
    distiller_output = ctx["inputs"].get("distiller", {})
    critic_output = ctx["inputs"].get("critic_agent", {})
    browser_output = ctx["inputs"].get("browser_comparison", {})
    plan = ctx["inputs"].get("planner", {})
    query = ctx["query"]

    items = distiller_output.get("items", [])
    critic_status = critic_output.get("status", "FAILED")
    ranking_criteria = plan.get("ranking_criteria", "likes")

    table_lines = [f"# Comparison Results: {query}", f"Critic Status: {critic_status}",
                   f"Ranking by: {ranking_criteria}", "",
                   "| Rank | Name | Likes | Downloads | Rating | Price | Source |",
                   "|------|------|-------|-----------|--------|-------|--------|"]

    for i, item in enumerate(items[:10]):
        rank = i + 1
        name = item.get("name", "Unknown")[:40]
        likes = item.get("likes", "N/A")
        downloads = item.get("downloads", "N/A")
        rating = item.get("rating", "N/A")
        price = item.get("price", "N/A")
        source = item.get("source_url", "")[:60]
        table_lines.append(f"| {rank} | {name} | {likes} | {downloads} | {rating} | {price} | {source} |")

    confidence = distiller_output.get("confidence", 0)
    table_lines.append("")
    table_lines.append(f"Extracted {len(items)} items with confidence {confidence:.2f}")

    answer = "\n".join(table_lines)

    browser_report = browser_output.get("report_data", {})
    path_durations = {k: v.get("duration_ms", 0) for k, v in browser_report.get("path_results", {}).items()}
    browser_duration = sum(path_durations.values())

    metrics = get_metrics_collector()
    if metrics._current:
        metrics._current.final_status = critic_status
        metrics._current.path_selected = browser_output.get("path", "")
        metrics._current.browser_duration_ms = browser_duration

    return {
        "answer": answer,
        "confidence": confidence,
        "items_count": len(items),
        "critic_status": critic_status,
        "ranking_criteria": ranking_criteria,
        "durations": {"planner": 0, "browser": browser_duration, "distiller": 0, "critic": 0, "total": browser_duration},
    }


async def node_replay_generator(ctx: dict[str, Any]) -> dict[str, Any]:
    """Generate replay report from comparison execution."""
    formatter_output = ctx["inputs"].get("formatter", {})
    distiller_output = ctx["inputs"].get("distiller", {})
    critic_output = ctx["inputs"].get("critic_agent", {})
    browser_output = ctx["inputs"].get("browser_comparison", {})
    query = ctx["query"]

    browser_report = browser_output.get("report_data", {})
    durations = formatter_output.get("durations", {})

    html, filepath = generate_replay_report(
        query=query,
        browser_report=browser_report,
        distiller_output=distiller_output,
        critic_output=critic_output,
        planner_duration=durations.get("planner", 0),
        browser_duration=durations.get("browser", 0),
        distiller_duration=durations.get("distiller", 0),
        critic_duration=durations.get("critic", 0),
        total_duration=durations.get("total", 0),
    )

    logger.info("Replay report generated: %s", filepath)
    return {"replay_html": html[:500], "replay_filepath": filepath, "replay_length": len(html)}
