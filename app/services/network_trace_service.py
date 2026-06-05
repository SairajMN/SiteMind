"""Network trace service — captures network requests during page load."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


async def capture_network_traces(
    url: str,
    page_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """Capture network traces (XHR, fetch, WebSocket, etc.) during page load using Playwright."""
    traces: list[dict[str, Any]] = []
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context()
                page = await context.new_page()

                collected: list[dict[str, Any]] = []

                async def on_request(req):
                    if req.resource_type in ("xhr", "fetch", "websocket"):
                        collected.append({
                            "url": req.url,
                            "method": req.method,
                            "resource_type": req.resource_type,
                            "headers": dict(req.headers),
                            "type": "request",
                        })

                async def on_response(resp):
                    if resp.request.resource_type in ("xhr", "fetch", "websocket"):
                        traces.append({
                            "url": resp.url,
                            "method": resp.request.method,
                            "resource_type": resp.request.resource_type,
                            "status_code": resp.status,
                            "headers": dict(resp.headers),
                            "type": "response",
                            "body_preview": str(await resp.text())[:2000] if resp.status < 400 else "",
                        })

                page.on("request", on_request)
                page.on("response", on_response)
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await context.close()
            finally:
                await browser.close()
    except ImportError:
        logger.warning("Playwright not available for network trace capture")
        return []
    except Exception as exc:
        logger.warning("Network trace capture failed for %s: %s", url, exc)
        return []

    return traces


def extract_endpoint_candidates(traces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract API endpoint candidates from network traces."""
    seen = set()
    candidates = []
    for t in traces:
        key = f"{t.get('method', 'GET')}:{t.get('url', '')}"
        if key in seen:
            continue
        seen.add(key)
        url = t.get("url", "")
        if any(ext in url for ext in [".css", ".js", ".png", ".jpg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"]):
            continue
        candidates.append({
            "request_url": url,
            "method": t.get("method", "GET"),
            "request_type": t.get("resource_type", "xhr"),
            "status_code": t.get("status_code"),
            "confidence": 0.7,
            "observation_type": "network_trace",
        })
    return candidates
