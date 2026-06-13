"""Web page visitor — uses Playwright to visit pages, capture screenshots and DOM."""

from __future__ import annotations

import logging
from typing import Any

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


async def visit_page(
    url: str,
    *,
    screenshot: bool = True,
    extract_dom: bool = True,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Visit a URL, capture screenshot and extract DOM structure.

    Returns:
        {
            "url": str,
            "title": str,
            "text_content": str (first 8000 chars),
            "screenshot_b64": str | None,
            "dom_elements": list[dict],
            "error": str | None,
            "success": bool,
        }
    """
    result: dict[str, Any] = {
        "url": url,
        "title": "",
        "text_content": "",
        "screenshot_b64": None,
        "dom_elements": [],
        "error": None,
        "success": False,
    }

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            # Navigate
            await page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            await page.wait_for_timeout(2000)

            # Title
            result["title"] = await page.title()

            # Text content
            text_content = await page.inner_text("body")
            result["text_content"] = text_content[:8000]

            # Screenshot
            if screenshot:
                screenshot_bytes = await page.screenshot(full_page=True, type="png")
                import base64
                result["screenshot_b64"] = base64.b64encode(screenshot_bytes).decode("utf-8")

            # DOM elements (structured extraction)
            if extract_dom:
                result["dom_elements"] = await _extract_dom_structured(page)

            # Product-specific detection
            result["detected_content_type"] = _detect_content_type(result["text_content"], result["dom_elements"])

            result["success"] = True
            logger.info("Page visit OK: %s (title=%s)", url, result["title"])

            await browser.close()

    except Exception as exc:
        logger.warning("Page visit failed for %s: %s", url, exc)
        result["error"] = str(exc)

    return result


async def _extract_dom_structured(page: Any) -> list[dict[str, Any]]:
    """Extract structured data from DOM using JavaScript."""
    try:
        elements = await page.evaluate("""() => {
            const items = [];

            // Extract product cards / listings
            const productSelectors = [
                '[class*="product"]', '[class*="card"]', '[class*="item"]',
                '[class*="listing"]', '[class*="result"]', 'li', 'tr',
                '[class*="grid"] > div', '[class*="row"] > div'
            ];

            document.querySelectorAll(productSelectors.join(',')).forEach(el => {
                const text = (el.innerText || '').trim().slice(0, 300);
                if (text.length < 15) return;

                const links = el.querySelectorAll('a');
                const images = el.querySelectorAll('img');
                const priceText = (el.innerText || '').match(/[\\u20B9\\$€£]\\s*[\\d,]+(?:\\.\\d+)?/);
                const ratingMatch = text.match(/([\\d.]+)\\s*(?:out of|\\/)\\s*5|(★|⭐)+/);

                // Check for price in text
                const hasPrice = /[\\u20B9\\$€£]\\s*[\\d,]+/.test(text);

                items.push({
                    text: text.slice(0, 200),
                    href: links.length > 0 ? links[0].href : '',
                    img: images.length > 0 ? images[0].src : '',
                    price: priceText ? priceText[0] : '',
                    hasPrice: hasPrice,
                    tag: el.tagName.toLowerCase(),
                    class: (el.className || '').slice(0, 80),
                    childCount: el.children.length,
                });
            });

            return items.slice(0, 30);
        }""")
        return elements
    except Exception as exc:
        logger.warning("DOM extraction failed: %s", exc)
        return []


def _detect_content_type(text: str, elements: list[dict[str, Any]]) -> str:
    """Detect what kind of content is on the page."""
    text_lower = text.lower()

    if any(w in text_lower for w in ["price", "₹", "$", "buy now", "add to cart", "specifications"]):
        return "ecommerce"
    if any(w in text_lower for w in ["sign in", "login", "password", "email"]):
        return "auth"
    if any(w in text_lower for w in ["search results", "found", "results for"]):
        return "search_results"
    if any(w in text_lower for w in ["compare", "comparison", "vs", "versus"]):
        return "comparison"
    if any(w in text_lower for w in ["blog", "article", "post", "published"]):
        return "article"
    if any(w in text_lower for w in ["review", "rating", "stars"]):
        return "review"

    return "general"