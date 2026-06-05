"""Screenshot service — captures page screenshots and analyzes them via Groq."""

from __future__ import annotations

import base64
import logging
import uuid
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def capture_and_analyze_screenshot(
    url: str,
    page_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Capture a screenshot using Playwright and analyze it."""
    settings = get_settings()
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                screenshot_bytes = await page.screenshot(full_page=False)
                title = await page.title()
                await context.close()
            finally:
                await browser.close()
    except ImportError:
        logger.warning("Playwright not available for screenshot capture")
        return {"summary": "Screenshot capture unavailable", "title": "", "skipped": True}
    except Exception as exc:
        logger.warning("Screenshot capture failed for %s: %s", url, exc)
        return {"summary": f"Screenshot capture failed: {exc}", "title": "", "skipped": True}

    b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
    analysis = await _analyze_screenshot(b64, title or url)

    return {
        "title": title or "",
        "summary": analysis.get("summary", ""),
        "layout_type": analysis.get("layout_type", "unknown"),
        "has_navbar": analysis.get("has_navbar", False),
        "has_sidebar": analysis.get("has_sidebar", False),
        "has_footer": analysis.get("has_footer", False),
        "skipped": False,
        "size_bytes": len(screenshot_bytes),
    }


async def _analyze_screenshot(b64_image: str, page_context: str) -> dict[str, Any]:
    """Use Groq vision to analyze screenshot content."""
    settings = get_settings()
    try:
        import httpx
        import json

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Describe this webpage screenshot ({page_context}). What layout, UI elements, navigation, forms, and visual structure do you see? Return JSON with: summary, layout_type, has_navbar (bool), has_sidebar (bool), has_footer (bool).",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{b64_image}",
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 512,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            return json.loads(data["choices"][0]["message"]["content"])
    except Exception as exc:
        logger.warning("Screenshot analysis failed: %s", exc)
        return {"summary": "Analysis unavailable", "layout_type": "unknown", "has_navbar": False, "has_sidebar": False, "has_footer": False}