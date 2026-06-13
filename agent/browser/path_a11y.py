"""Path 3: Accessibility — Accessible Tree extraction via ARIA roles.

Used when DOM is complex (React apps, dynamic dashboards, JS-heavy interfaces)."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.browser.action_logger import ActionLogger
from agent.browser.screenshot_manager import ScreenshotManager

logger = logging.getLogger(__name__)


async def try_a11y(
    url: str,
    page: Any,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Navigate and extract content using Accessibility Tree."""
    result: dict[str, Any] = {
        "path": "a11y",
        "url": url,
        "success": False,
        "content": "",
        "title": "",
        "a11y_tree": [],
        "error": None,
    }

    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, "a11y_navigate")
        if action_logger:
            action_logger.log_navigate(url)

        await page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
        await page.wait_for_timeout(2000)

        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, "a11y_loaded")
        if action_logger:
            action_logger.log_action("a11y_page_loaded", target=url, url=url)

        title = await page.title()
        result["title"] = title

        # Try accessibility snapshot
        a11y_snapshot = await page.accessibility.snapshot()
        if a11y_snapshot:
            tree_text = _flatten_a11y_tree(a11y_snapshot)
            result["a11y_tree"] = tree_text[:8000]
            result["content"] = tree_text[:8000]
            result["success"] = True
            result["nodes_count"] = _count_nodes(a11y_snapshot)

        # Also get ARIA labels and roles
        aria_info = await _extract_aria_info(page)
        if aria_info:
            result["aria_roles"] = aria_info["roles"]
            result["aria_labels"] = aria_info["labels"]

        logger.info(
            "Path A11Y: %s for %s (nodes=%d)",
            "success" if result["success"] else "failed",
            url,
            result.get("nodes_count", 0),
        )
        return result

    except Exception as exc:
        logger.warning("Path A11Y: failed for %s: %s", url, exc)
        result["error"] = str(exc)
        if screenshot_mgr:
            await screenshot_mgr.capture_failure(page, "a11y_failure")
        return result


async def _extract_aria_info(page: Any) -> dict[str, Any] | None:
    """Extract ARIA roles and labels from the page."""
    try:
        roles = await page.evaluate("""() => {
            const els = document.querySelectorAll('[role]');
            const roles = {};
            els.forEach(el => {
                const r = el.getAttribute('role');
                if (r) roles[r] = (roles[r] || 0) + 1;
            });
            return roles;
        }""")

        labels = await page.evaluate("""() => {
            const els = document.querySelectorAll('[aria-label]');
            return els.length;
        }""")

        return {"roles": roles, "labels": labels}
    except Exception:
        return None


def _flatten_a11y_tree(node: dict[str, Any], depth: int = 0) -> str:
    """Flatten accessibility tree to readable text."""
    lines = []
    indent = "  " * depth
    name = node.get("name", "")
    role = node.get("role", "")
    if name and role:
        lines.append(f"{indent}[{role}] {name}")
    elif role:
        lines.append(f"{indent}[{role}]")
    for child in node.get("children", []):
        if isinstance(child, dict):
            child_text = _flatten_a11y_tree(child, depth + 1)
            if child_text:
                lines.append(child_text)
    return "\n".join(lines)


def _count_nodes(node: dict[str, Any]) -> int:
    """Count total nodes in accessibility tree."""
    count = 1
    for child in node.get("children", []):
        if isinstance(child, dict):
            count += _count_nodes(child)
    return count


def can_a11y(url: str, task_type: str = "") -> float:
    """Score whether a11y path is viable (0.0 to 1.0)."""
    js_frameworks = ["react", "vue", "angular", "svelte", "next", "nuxt", "gatsby"]
    for fw in js_frameworks:
        if fw in url.lower():
            return 0.8
    return 0.5
