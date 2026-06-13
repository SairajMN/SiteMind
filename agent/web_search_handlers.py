"""Web Search DAG handlers — searches the web, visits pages, analyzes with VLM + DOM."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.web_search.page_visitor import visit_page
from agent.web_search.search_engine import search_web
from agent.web_search.vlm_client import analyze_text_with_llm, analyze_with_vlm

logger = logging.getLogger(__name__)


async def node_web_search_planner(ctx: dict[str, Any]) -> dict[str, Any]:
    """Plan the web search — classify query and determine extraction strategy."""
    query = ctx["query"].strip()

    # Use LLM to generate optimal search queries and extraction plan
    plan_prompt = (
        f"Given the user query: '{query}'\n\n"
        "Generate a search plan with:\n"
        "1. search_query: optimized search query for DuckDuckGo\n"
        "2. extraction_fields: what data to extract (e.g., price, rating, specs)\n"
        "3. max_sites: how many sites to visit (3-5)\n"
        "4. comparison_type: 'product', 'service', 'general', or 'info'\n\n"
        "Return ONLY valid JSON, no markdown."
    )

    llm_result = await analyze_text_with_llm(plan_prompt)
    plan = {}
    if llm_result:
        try:
            import re
            json_match = re.search(r"\{.*\}", llm_result, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group(0))
        except Exception:
            pass

    # Fallback plan
    if not plan.get("search_query"):
        plan = {
            "search_query": query,
            "extraction_fields": ["name", "price", "rating", "description"],
            "max_sites": 5,
            "comparison_type": "product" if any(w in query.lower() for w in ["price", "buy", "best", "top", "under", "compare", "vs"]) else "general",
        }

    logger.info("Web search plan: query=%s sites=%d type=%s",
                plan["search_query"], plan["max_sites"], plan.get("comparison_type", "general"))
    return {
        "original_query": query,
        "search_query": plan["search_query"],
        "extraction_fields": plan.get("extraction_fields", ["name", "price", "rating"]),
        "max_sites": min(plan.get("max_sites", 5), 10),
        "comparison_type": plan.get("comparison_type", "general"),
    }


async def node_web_searcher(ctx: dict[str, Any]) -> dict[str, Any]:
    """Execute the web search and return ranked results."""
    plan = ctx["inputs"]["planner"]
    search_query = plan["search_query"]
    max_results = plan.get("max_sites", 5) * 2  # get twice as many to filter

    results = await search_web(search_query, max_results=max_results)

    logger.info("Web search returned %d results for '%s'", len(results), search_query)

    return {
        "search_results": results,
        "total_found": len(results),
        "search_query_used": search_query,
    }


async def node_web_page_visitor(ctx: dict[str, Any]) -> dict[str, Any]:
    """Visit top search result pages in parallel and extract data."""
    searcher = ctx["inputs"]["searcher"]
    plan = ctx["inputs"]["planner"]
    results = searcher["search_results"]
    max_sites = plan.get("max_sites", 5)

    # Take top N results
    urls_to_visit = [r["url"] for r in results[:max_sites] if r.get("url")]

    logger.info("Visiting %d pages in parallel", len(urls_to_visit))

    import asyncio
    tasks = [visit_page(url) for url in urls_to_visit]
    page_data_list = await asyncio.gather(*tasks, return_exceptions=True)

    successful_pages = []
    for i, page_data in enumerate(page_data_list):
        if isinstance(page_data, Exception):
            logger.warning("Page visit error for %s: %s", urls_to_visit[i] if i < len(urls_to_visit) else "unknown", page_data)
            continue
        if page_data.get("success"):
            successful_pages.append(page_data)

    logger.info("Successfully visited %d/%d pages", len(successful_pages), len(urls_to_visit))

    return {
        "pages": successful_pages,
        "total_visited": len(urls_to_visit),
        "successful": len(successful_pages),
    }


async def node_web_vlm_analyzer(ctx: dict[str, Any]) -> dict[str, Any]:
    """Analyze each visited page with VLM (screenshot + DOM) for structured extraction."""
    visitor = ctx["inputs"]["visitor"]
    plan = ctx["inputs"]["planner"]
    pages = visitor["pages"]
    extraction_fields = plan.get("extraction_fields", ["name", "price", "rating"])
    comparison_type = plan.get("comparison_type", "general")

    extraction_instructions = (
        f"Extract {comparison_type} data from this page. "
        f"Fields to extract: {', '.join(extraction_fields)}. "
        "For each item, provide name, price, rating, specs, and source_url."
    )

    import asyncio

    async def analyze_page(page_data: dict[str, Any]) -> dict[str, Any]:
        screenshot_b64 = page_data.get("screenshot_b64")
        image_bytes = None
        if screenshot_b64:
            import base64
            try:
                image_bytes = base64.b64decode(screenshot_b64)
            except Exception:
                pass

        vlm_result = await analyze_with_vlm(
            image_bytes=image_bytes,
            page_text=page_data.get("text_content", ""),
            extraction_instructions=extraction_instructions,
        )

        # Fallback: if VLM extracted nothing, parse DOM elements directly
        if not vlm_result.get("extracted"):
            vlm_result["extracted"] = _extract_from_dom(page_data.get("dom_elements", []))
            if vlm_result["extracted"]:
                vlm_result["summary"] = f"Extracted {len(vlm_result['extracted'])} items from DOM"
                vlm_result["source"] = "dom_fallback"

        return {
            "url": page_data["url"],
            "title": page_data.get("title", ""),
            "vlm_analysis": vlm_result,
            "dom_elements": page_data.get("dom_elements", []),
            "detected_content_type": page_data.get("detected_content_type", "general"),
        }

    tasks = [analyze_page(page) for page in pages]
    analyzed_pages = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for r in analyzed_pages:
        if isinstance(r, Exception):
            logger.warning("VLM analysis error: %s", r)
            continue
        results.append(r)

    # Merge all extracted items
    all_items = []
    for page_result in results:
        for item in page_result.get("vlm_analysis", {}).get("extracted", []):
            item["source_url"] = page_result["url"]
            item["page_title"] = page_result["title"]
            all_items.append(item)

    logger.info("VLM extracted %d items from %d pages", len(all_items), len(results))

    return {
        "analyzed_pages": results,
        "extracted_items": all_items,
        "total_analyzed": len(results),
    }


async def node_web_search_formatter(ctx: dict[str, Any]) -> dict[str, Any]:
    """Format the final answer with comparison data."""
    vlm = ctx["inputs"]["vlm"]
    plan = ctx["inputs"]["planner"]
    searcher = ctx.get("inputs", {}).get("searcher", {})

    items = vlm.get("extracted_items", [])
    pages = vlm.get("analyzed_pages", [])
    query = plan.get("original_query", "")

    # Build a markdown-style answer
    lines = [
        f"## Web Search Results: {query}",
        "",
        f"Found {len(items)} items across {len(pages)} pages.",
        "",
    ]

    # Build comparison table
    if items:
        lines.append("| # | Name | Price | Rating | Source |")
        lines.append("|---|---|---|---|---|")
        for i, item in enumerate(items[:15], 1):
            name = (item.get("name") or "N/A")[:40]
            price = (item.get("price") or item.get("pricing") or "N/A")[:20]
            rating = (item.get("rating") or item.get("ratings") or "N/A")[:15]
            source = (item.get("source_url") or item.get("page_title") or "N/A")[:40]
            lines.append(f"| {i} | {name} | {price} | {rating} | {source} |")

    lines.append("")

    # Page summaries
    if pages:
        lines.append("### Pages Analyzed")
        lines.append("")
        for p in pages:
            lines.append(f"- **{p.get('title', 'N/A')}** ({p['url']})")
            summary = p.get("vlm_analysis", {}).get("summary", "")
            if summary:
                lines.append(f"  - {summary[:200]}")

    final_answer = "\n".join(lines)

    # Build structured comparison items for the frontend
    comparison_items = []
    for item in items[:15]:
        comparison_items.append({
            "rank": str(comparison_items.count(None) + 1),
            "name": item.get("name", "N/A"),
            "price": item.get("price", item.get("pricing", "N/A")),
            "rating": item.get("rating", item.get("ratings", "N/A")),
            "specs": item.get("specs", item.get("description", "")),
            "source": item.get("source_url", ""),
            "page_title": item.get("page_title", ""),
        })

    return {
        "answer": final_answer,
        "comparison_table": comparison_items,
        "total_items": len(items),
        "total_pages": len(pages),
    }


def _extract_from_dom(dom_elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse DOM elements for product-like items when VLM fails."""
    items = []
    for el in dom_elements:
        if not el.get("hasPrice") and not el.get("price"):
            continue
        text = el.get("text", "")
        if len(text) < 15:
            continue
        price = el.get("price", "")
        if not price:
            import re
            m = re.search(r"[\u20B9$]\s*[\d,]+(?:\.\d+)?", text)
            price = m.group(0) if m else ""
        rating = ""
        import re
        rm = re.search(r"[\d.]+\s*(?:out of|/)\s*5|[\u2605]+", text)
        if rm:
            rating = rm.group(0)
        name = text.split("\n")[0][:80] if text else ""
        items.append({
            "name": name,
            "price": price,
            "rating": rating,
            "specs": "",
            "source_url": el.get("href", ""),
        })
    return items[:15]
