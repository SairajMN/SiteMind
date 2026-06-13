"""Path 1: Extract — HTTP fetch, Trafilatura, Readability, static HTML parsing.

Used when content is directly available through simple HTTP fetch without browser."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def try_extract(
    url: str,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Try to extract content via HTTP fetch and static HTML parsing.

    Returns dict with path info and extracted content or error.
    """
    result: dict[str, Any] = {
        "path": "extract",
        "url": url,
        "success": False,
        "content": "",
        "title": "",
        "error": None,
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

            # Extract title
            import re
            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
            )
            title = title_match.group(1).strip() if title_match else ""

            # Try Readability-like extraction (basic text extraction)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # Remove scripts, styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Limit to first 8000 chars
            text = text[:8000]

            result["success"] = True
            result["content"] = text
            result["title"] = title
            result["content_length"] = len(text)
            result["extraction_method"] = "http_fetch_bs4"

            logger.info(
                "Path EXTRACT: success for %s (%d chars)", url, len(text)
            )
            return result

    except httpx.TimeoutException:
        logger.warning("Path EXTRACT: timeout for %s", url)
        result["error"] = "HTTP timeout"
    except httpx.HTTPStatusError as exc:
        logger.warning("Path EXTRACT: HTTP %s for %s", exc.response.status_code, url)
        result["error"] = f"HTTP {exc.response.status_code}"
    except Exception as exc:
        logger.warning("Path EXTRACT: failed for %s: %s", url, exc)
        result["error"] = str(exc)

    return result


def can_extract(url: str, task_type: str = "") -> float:
    """Score whether extract path is viable (0.0 to 1.0).

    Static content, public APIs, and docs score high.
    JS-heavy SPAs score low.
    """
    # Dynamic/JS-heavy sites are poor candidates for extraction
    js_indicators = ["app", "spa", "react", "vue", "angular", "dashboard"]
    for indicator in js_indicators:
        if indicator in url.lower():
            return 0.3

    # Static content sites are good candidates
    static_indicators = [
        "docs", "blog", "news", "wiki", "wikipedia", "github.com",
        "arxiv", "pypi", "npmjs",
    ]
    for indicator in static_indicators:
        if indicator in url.lower():
            return 0.9

    # Default moderate score
    return 0.6
