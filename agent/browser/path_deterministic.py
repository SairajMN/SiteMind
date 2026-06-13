"""Path 2: Deterministic — Playwright with CSS/XPath selectors, table extraction.

Used when structured selectors exist (product cards, tables, listings)."""

from __future__ import annotations

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from agent.browser.screenshot_manager import ScreenshotManager
from agent.browser.action_logger import ActionLogger

logger = logging.getLogger(__name__)


async def try_deterministic(
    url: str,
    page: Any,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Navigate and extract content using Playwright with CSS/XPath selectors."""
    result: dict[str, Any] = {
        "path": "deterministic",
        "url": url,
        "success": False,
        "content": "",
        "title": "",
        "html_snippet": "",
        "items": [],
        "actions": [],
        "error": None,
    }

    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, "navigate_to_page")
        if action_logger:
            action_logger.log_navigate(url)

        await page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
        await page.wait_for_timeout(1000)

        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, "page_loaded")
        if action_logger:
            action_logger.log_action("page_loaded", target=url, url=url)

        title = await page.title()
        content = await page.content()
        text_content = await page.inner_text("body")

        result["success"] = True
        result["title"] = title
        result["content"] = text_content[:8000]
        result["html_snippet"] = content[:5000]
        result["content_length"] = len(text_content)

        tables = await _extract_tables(page)
        if tables:
            result["tables"] = tables

        cards = await _extract_product_cards(page)
        if cards:
            result["items"] = cards

        lists = await _extract_listings(page)
        if lists:
            result["listings"] = lists

        logger.info(
            "Path DETERMINISTIC: success for %s (title=%s, items=%d)",
            url, title, len(result.get("items", [])),
        )
        return result

    except Exception as exc:
        logger.warning("Path DETERMINISTIC: failed for %s: %s", url, exc)
        result["error"] = str(exc)
        if screenshot_mgr:
            await screenshot_mgr.capture_failure(page, "deterministic_failure")
        return result


async def try_search(
    page: Any,
    search_query: str,
    search_selector: str = "input[type='search'], input[name='search']",
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
) -> dict[str, Any]:
    if action_logger:
        action_logger.log_search(search_query, url=page.url)
    try:
        si = await page.query_selector(search_selector)
        if not si:
            si = await page.query_selector("input[type='text']")
        if not si:
            return {"success": False, "error": "No search input"}
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, f"search_{search_query}")
        await si.click()
        await si.fill(search_query)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, f"results_{search_query}")
        if action_logger:
            action_logger.log_action("search_complete", target=search_query, url=page.url, status="success")
        return {"success": True, "url": page.url, "title": await page.title()}
    except Exception as exc:
        if action_logger:
            action_logger.log_failure("search", search_query, url=page.url, error=str(exc))
        if screenshot_mgr:
            await screenshot_mgr.capture_failure(page, f"search_failed_{search_query}")
        return {"success": False, "error": str(exc)}


async def try_open_detail(
    page: Any,
    item_selector: str = "a[href], .card a, .item a, h2 a, h3 a",
    index: int = 0,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
) -> dict[str, Any]:
    """Open a detail page by clicking the indexed item link."""
    try:
        links = await page.query_selector_all(item_selector)
        if index >= len(links):
            return {"success": False, "error": f"Index {index} out of range ({len(links)})"}
        link = links[index]
        href = await link.get_attribute("href")
        text = await link.inner_text()
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, f"detail_{text[:30]}")
        if action_logger:
            action_logger.log_open_detail(text[:50], url=page.url)
        async with page.expect_navigation(timeout=15000, wait_until="networkidle"):
            await link.click()
        await page.wait_for_timeout(1000)
        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, f"detail_page_{text[:30]}")
        if action_logger:
            action_logger.log_action("detail_opened", target=text[:50], url=page.url, status="success")
        return {"success": True, "title": await page.title(), "url": page.url, "item_text": text[:100], "href": href}
    except Exception as exc:
        if action_logger:
            action_logger.log_failure("open_detail", str(index), url=page.url, error=str(exc))
        if screenshot_mgr:
            await screenshot_mgr.capture_failure(page, "detail_failure")
        return {"success": False, "error": str(exc)}


async def try_paginate(
    page: Any,
    page_num: int = 2,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
) -> dict[str, Any]:
    """Go to the next page of results."""
    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, f"paginate_{page_num}")
        if action_logger:
            action_logger.log_paginate(page_num, url=page.url)
        next_sel = "a.next, button.next, [aria-label='Next'], a:has-text('Next')"
        nb = await page.query_selector(next_sel)
        if not nb:
            pl = await page.query_selector_all(f"a:has-text('{page_num}')")
            if pl:
                async with page.expect_navigation(timeout=15000, wait_until="networkidle"):
                    await pl[0].click()
                await page.wait_for_timeout(1000)
            else:
                return {"success": False, "error": "No pagination"}
        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, f"page_{page_num}")
        if action_logger:
            action_logger.log_action("paginated", target=str(page_num), url=page.url, status="success")
        return {"success": True, "url": page.url, "page": page_num}
    except Exception as exc:
        if action_logger:
            action_logger.log_failure("paginate", str(page_num), url=page.url, error=str(exc))
        return {"success": False, "error": str(exc)}


async def try_click_sort(
    page: Any,
    sort_text: str = "Likes",
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
) -> dict[str, Any]:
    """Click a sort option by text content."""
    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, f"sort_{sort_text}")
        if action_logger:
            action_logger.log_sort(sort_text, url=page.url)
        selectors = [
            f"text={sort_text}",
            f"//*[contains(text(), '{sort_text}')]",
            f"button:has-text('{sort_text}')",
            f"a:has-text('{sort_text}')",
            f"th:has-text('{sort_text}')",
            f"span:has-text('{sort_text}')",
            f"[aria-label*='{sort_text}']",
        ]
        clicked = False
        for sel in selectors:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    await elem.click()
                    await page.wait_for_timeout(1500)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    clicked = True
                    break
            except Exception:
                continue
        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, f"sorted_{sort_text}")
        if action_logger:
            action_logger.log_action("sort_click", target=sort_text, url=page.url, status="success" if clicked else "not_found")
        return {"success": clicked, "url": page.url}
    except Exception as exc:
        if action_logger:
            action_logger.log_failure("sort", sort_text, url=page.url, error=str(exc))
        return {"success": False, "error": str(exc)}


async def try_click_filter(
    page: Any,
    filter_text: str,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
) -> dict[str, Any]:
    """Click a filter option by text content."""
    try:
        if screenshot_mgr:
            await screenshot_mgr.capture_before(page, f"filter_{filter_text}")
        if action_logger:
            action_logger.log_filter(filter_text, url=page.url)
        selectors = [
            f"text={filter_text}",
            f"//*[contains(text(), '{filter_text}')]",
            f"label:has-text('{filter_text}')",
            f"a:has-text('{filter_text}')",
            f"[data-filter*='{filter_text}']",
        ]
        clicked = False
        for sel in selectors:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    await elem.click()
                    await page.wait_for_timeout(1000)
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    clicked = True
                    break
            except Exception:
                continue
        if screenshot_mgr:
            await screenshot_mgr.capture_after(page, f"filtered_{filter_text}")
        if action_logger:
            action_logger.log_action("filter_click", target=filter_text, url=page.url, status="success" if clicked else "not_found")
        return {"success": clicked, "url": page.url}
    except Exception as exc:
        if action_logger:
            action_logger.log_failure("filter", filter_text, url=page.url, error=str(exc))
        return {"success": False, "error": str(exc)}


async def _extract_tables(page: Any) -> list[dict[str, Any]]:
    """Extract HTML tables from the page."""
    tables = []
    try:
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        for i, table_tag in enumerate(soup.find_all("table")):
            rows = []
            headers = []
            for th in table_tag.find_all("th"):
                headers.append(th.get_text(strip=True))
            for tr in table_tag.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({"index": i, "headers": headers, "rows": rows[:20]})
    except Exception:
        pass
    return tables


async def _extract_product_cards(page: Any) -> list[dict[str, Any]]:
    """Extract product/model cards using common card selectors."""
    items = []
    try:
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        card_selectors = [
            "article", ".card", ".product-card", ".model-card",
            ".repo-card", ".item", ".listing-item", ".result-item",
            "[class*='card']", "[class*='Card']", "[class*='product']",
            "[class*='model']", "[class*='repo']",
        ]
        for selector in card_selectors:
            cards = soup.select(selector)
            for card in cards:
                item = _parse_card(card)
                if item and item.get("name"):
                    items.append(item)
            if len(items) >= 10:
                break
    except Exception:
        pass
    return items


async def _extract_listings(page: Any) -> list[dict[str, Any]]:
    """Extract structured listings."""
    listings = []
    try:
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")
        list_selectors = [
            "ul li", "ol li", "[class*='list'] li", "[class*='List'] li",
            "[class*='grid'] > *", "[class*='Grid'] > *",
            "[class*='results'] > *", "[class*='Results'] > *",
        ]
        for selector in list_selectors:
            items = soup.select(selector)
            if len(items) > 3:
                for item in items[:20]:
                    text = item.get_text(strip=True)[:200]
                    link = item.find("a")
                    href = link.get("href", "") if link else ""
                    if text and len(text) > 10:
                        listings.append({"text": text, "href": href, "html": str(item)[:500]})
            if listings:
                break
    except Exception:
        pass
    return listings


def _parse_card(card: Any) -> dict[str, Any] | None:
    """Parse a card element for name, score, metadata."""
    try:
        name_tag = card.find(["h1", "h2", "h3", "h4", "a", "strong", "span"])
        name = name_tag.get_text(strip=True) if name_tag else ""
        score_tag = card.find(class_=re.compile(r"(score|rating|likes|downloads|price|cost)", re.I))
        score = score_tag.get_text(strip=True) if score_tag else ""
        link = card.find("a")
        href = link.get("href", "") if link else ""
        desc_tag = card.find(["p", "div", "span"], class_=re.compile(r"(desc|summary|text|about)", re.I))
        description = desc_tag.get_text(strip=True)[:200] if desc_tag else ""
        if not name:
            return None
        result = {"name": name}
        if href:
            result["href"] = href
        if score:
            result["score"] = score
        if description:
            result["description"] = description
        text = card.get_text()
        likes = re.search(r"(\d+[kKmM]?)\s*(likes|❤|♥|⭐|★)", text, re.I)
        if likes:
            result["likes"] = likes.group(1)
        downloads = re.search(r"(\d+[kKmM]?)\s*(downloads|installs|users)", text, re.I)
        if downloads:
            result["downloads"] = downloads.group(1)
        price = re.search(r"(\$[\d.]+|€[\d.]+|£[\d.]+)", text)
        if price:
            result["price"] = price.group(1)
        rating = re.search(r"([\d.]+)\s*/\s*5", text)
        if rating:
            result["rating"] = rating.group(1)
        return result
    except Exception:
        return None


def can_deterministic(url: str, task_type: str = "") -> float:
    """Score whether deterministic path is viable (0.0 to 1.0)."""
    structured_sites = [
        "huggingface.co", "github.com", "pypi.org", "npmjs.com",
        "amazon.com", "amazon.in", "flipkart.com", "ebay.com",
        "wikipedia.org", "imdb.com", "producthunt.com",
        "g2.com", "capterra.com", "getapp.com",
        "stackoverflow.com", "medium.com", "dev.to",
    ]
    for site in structured_sites:
        if site in url.lower():
            return 0.95
    return 0.7
