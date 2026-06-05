from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import same_domain
from app.crawler.frontier import CrawlFrontier
from app.crawler.page_fetcher import FetchedPage, fetch_page, filter_same_domain
from app.models.orm import AuthSignal, CrawlJob, Endpoint, Form, FormField, Page, Site

logger = logging.getLogger(__name__)


async def run_crawl(
    session: AsyncSession,
    *,
    site: Site,
    job: CrawlJob,
    use_playwright: bool = True,
) -> dict[str, int]:
    settings = get_settings()
    frontier = CrawlFrontier(
        site.root_url,
        max_depth=job.requested_depth,
        page_budget=job.page_budget,
    )
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await session.flush()

    pages: list[FetchedPage] = []
    counts = {"pages": 0, "forms": 0, "endpoints": 0, "auth_signals": 0}

    while True:
        item = frontier.pop()
        if item is None:
            break
        url, depth = item
        if not same_domain(url, site.root_url):
            continue
        if not frontier.is_seen(url):
            continue
        try:
            fetched = await fetch_page(url, depth, use_playwright=use_playwright)
        except Exception as exc:
            logger.warning("Skip %s: %s", url, exc)
            continue

        page_row = Page(
            site_id=site.id,
            crawl_job_id=job.id,
            url=fetched.url,
            canonical_url=fetched.canonical_url,
            title=fetched.title,
            depth=fetched.depth,
            path=urlparse_path(fetched.url),
            status_code=fetched.status_code,
            content_hash=fetched.content_hash,
            has_form=fetched.has_form,
            has_auth_hint=fetched.has_auth_hint,
        )
        session.add(page_row)
        await session.flush()
        pages.append(fetched)
        counts["pages"] += 1

        if fetched.has_form:
            await _extract_forms(session, page_row, fetched)
            counts["forms"] += 1
        if fetched.has_auth_hint:
            session.add(
                AuthSignal(
                    page_id=page_row.id,
                    signal_type="login_hint",
                    signal_value="text_match",
                    confidence=0.7,
                )
            )
            counts["auth_signals"] += 1

        internal = filter_same_domain(site.root_url, fetched.links)
        for link in internal[:30]:
            if link.endswith((".css", ".js", ".png", ".jpg", ".gif", ".svg", ".ico")):
                continue
            session.add(
                Endpoint(
                    page_id=page_row.id,
                    request_url=link,
                    method="GET",
                    request_type="navigation",
                    status_code=None,
                    observation_type="observed",
                    confidence=0.6,
                )
            )
            counts["endpoints"] += 1

        frontier.add_links(url, internal, depth)

    job.status = "completed"
    job.finished_at = datetime.now(timezone.utc)
    await session.flush()
    return counts


def urlparse_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path or "/"


async def _extract_forms(session: AsyncSession, page_row: Page, fetched: FetchedPage) -> None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(fetched.html, "lxml")
    for idx, form_el in enumerate(soup.find_all("form")):
        form = Form(
            page_id=page_row.id,
            form_index=idx,
            action_url=form_el.get("action"),
            method=(form_el.get("method") or "get").upper(),
            confidence=0.85,
        )
        session.add(form)
        await session.flush()
        for inp in form_el.find_all(["input", "textarea", "select"]):
            session.add(
                FormField(
                    form_id=form.id,
                    name=inp.get("name"),
                    label=inp.get("aria-label") or inp.get("placeholder"),
                    field_type=inp.get("type") or inp.name,
                    required=inp.has_attr("required"),
                    placeholder=inp.get("placeholder"),
                )
            )
