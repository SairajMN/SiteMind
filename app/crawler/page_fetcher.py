from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.core.security import same_domain, sanitize_html

logger = logging.getLogger(__name__)


@dataclass
class FetchedPage:
    url: str
    canonical_url: str
    title: str | None
    depth: int
    status_code: int
    content_hash: str
    html: str
    text: str
    headings: list[str]
    links: list[str]
    has_form: bool
    has_auth_hint: bool


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


def _auth_hint(soup: BeautifulSoup) -> bool:
    blob = soup.get_text(" ", strip=True).lower()
    return any(k in blob for k in ("login", "sign in", "password", "register"))


async def fetch_page_playwright(url: str, depth: int, timeout_ms: int = 30000) -> FetchedPage:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True,
            )
            page = await context.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                html = await page.content()
                title = await page.title()
                status = response.status if response else 0
            finally:
                await context.close()
        finally:
            await browser.close()

    return _parse_html(url, html, title, status, depth)


def fetch_page_http(url: str, depth: int) -> FetchedPage:
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    with httpx.Client(follow_redirects=True, timeout=30.0, headers=headers) as client:
        response = client.get(url)
        html = response.text
        status = response.status_code
    return _parse_html(url, html, None, status, depth)


def _parse_html(
    url: str, html: str, title: str | None, status: int, depth: int
) -> FetchedPage:
    soup = BeautifulSoup(html, "lxml")
    if not title:
        t = soup.find("title")
        title = t.get_text(strip=True) if t else None
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])][:20]
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("javascript:"):
            continue
        links.append(urljoin(url, href))
    text = soup.get_text(" ", strip=True)[:8000]
    safe = sanitize_html(html[:50000])
    return FetchedPage(
        url=url,
        canonical_url=url,
        title=title,
        depth=depth,
        status_code=status,
        content_hash=_content_hash(safe),
        html=safe,
        text=text,
        headings=headings,
        links=links,
        has_form=bool(soup.find("form")),
        has_auth_hint=_auth_hint(soup),
    )


async def fetch_page(url: str, depth: int, use_playwright: bool = True) -> FetchedPage:
    if use_playwright:
        try:
            return await fetch_page_playwright(url, depth)
        except Exception:
            logger.warning("Playwright failed for %s, falling back to httpx", url)
    return fetch_page_http(url, depth)


def filter_same_domain(root_url: str, links: list[str]) -> list[str]:
    return [u for u in links if same_domain(u, root_url)]
