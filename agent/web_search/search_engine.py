"""DuckDuckGo web search engine — completely free, no API key required."""

from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def search_duckduckgo(query: str, max_results: int = 10) -> list[dict[str, str]]:
    """Search DuckDuckGo and return a list of {title, url, snippet} results."""
    params = {"q": query.strip()}
    results: list[dict[str, str]] = []

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            resp = await client.post(
                DUCKDUCKGO_URL,
                data=params,
                headers=REQUEST_HEADERS,
            )
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("DuckDuckGo search failed: %s", exc)
            return results

        # Parse results from HTML
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".result"):
                title_el = item.select_one(".result__title a")
                snippet_el = item.select_one(".result__snippet")

                if title_el:
                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    # DuckDuckGo wraps redirects
                    if "uddg=" in str(href):
                        parsed = urllib.parse.urlparse(str(href))
                        qs = urllib.parse.parse_qs(parsed.query)
                        actual_url = qs.get("uddg", [""])[0]
                    else:
                        actual_url = str(href)
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    if title and actual_url:
                        results.append({
                            "title": title,
                            "url": actual_url,
                            "snippet": snippet,
                        })

            if len(results) >= max_results:
                results = results[:max_results]

            logger.info("DuckDuckGo returned %d results for query=%r", len(results), query)
        except Exception as exc:
            logger.warning("Failed to parse DuckDuckGo results: %s", exc)

    return results


async def search_web(query: str, max_results: int = 10) -> list[dict[str, str]]:
    """High-level web search — currently DuckDuckGo, can be swapped."""
    return await search_duckduckgo(query, max_results=max_results)