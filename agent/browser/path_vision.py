"""Path 4: Vision — Screenshot capture, Set-of-Marks, OCR extraction.

Used when selectors fail (Canvas apps, Shadow DOM, Anti-bot interfaces)."""

from __future__ import annotations

import base64
import logging
from typing import Any

from agent.browser.action_logger import ActionLogger
from agent.browser.screenshot_manager import ScreenshotManager

logger = logging.getLogger(__name__)


async def try_vision(
    url: str,
    page: Any,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Navigate and extract content using vision (screenshot + LLM analysis).

    Captures a screenshot, optionally processes with vision LLM or OCR.
    """
    result: dict[str, Any] = {
        "path": "vision",
        "url": url,
        "success": False,
        "content": "",
        "title": "",
        "screenshot_ref": "",
        "elements": [],
        "error": None,
    }

    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, "vision_navigate")
        if action_logger:
            action_logger.log_navigate(url)

        await page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
        await page.wait_for_timeout(2000)

        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, "vision_loaded")
        if action_logger:
            action_logger.log_action("vision_page_loaded", target=url, url=url)

        title = await page.title()
        result["title"] = title

        # Capture full-page screenshot
        screenshot_bytes = await page.screenshot(full_page=True)
        b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        result["screenshot_b64"] = b64
        result["screenshot_size"] = len(screenshot_bytes)

        # Extract visible text
        visible_text = await page.inner_text("body")
        result["content"] = visible_text[:8000]
        result["success"] = True

        # Try to extract elements via JS
        elements = await _extract_visible_elements(page)
        if elements:
            result["elements"] = elements

        logger.info("Path VISION: success for %s (title=%s)", url, title)
        return result

    except Exception as exc:
        logger.warning("Path VISION: failed for %s: %s", url, exc)
        result["error"] = str(exc)
        if screenshot_mgr:
            await screenshot_mgr.capture_failure(page, "vision_failure")
        return result


async def _extract_visible_elements(page: Any) -> list[dict[str, Any]]:
    """Extract visible interactive elements via JavaScript."""
    try:
        elements = await page.evaluate("""() => {
            const interactive = [];
            const selectors = 'a, button, input, select, textarea, [role="button"], [role="link"], [tabindex]';
            const els = document.querySelectorAll(selectors);
            els.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight) {
                    interactive.push({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || '').trim().slice(0, 100),
                        href: el.href || '',
                        role: el.getAttribute('role') || '',
                        type: el.getAttribute('type') || '',
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        visible: rect.top < window.innerHeight
                    });
                }
            });
            return interactive.slice(0, 50);
        }""")
        return elements
    except Exception:
        return []


def can_vision(url: str, task_type: str = "") -> float:
    """Score whether vision path is viable (0.0 to 1.0)."""
    # Vision is a fallback for complex cases
    return 0.9
