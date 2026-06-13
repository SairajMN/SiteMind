"""BrowserEngine — multi-path browser execution with automatic path selection.

Chooses the cheapest successful path:
  1. Extract (HTTP fetch, no browser)
  2. Deterministic (Playwright + CSS/XPath)
  3. A11y (Accessibility Tree)
  4. Vision (Screenshot + LLM/OCR)
  5. Blocked (Detection + graceful failure)
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any

from agent.browser.action_logger import ActionLogger, create_action_logger
from agent.browser.path_a11y import can_a11y, try_a11y
from agent.browser.path_blocked import suggest_recovery, try_detect_blocked
from agent.browser.path_deterministic import (
    can_deterministic,
    try_click_filter,
    try_click_sort,
    try_deterministic,
    try_open_detail,
    try_paginate,
    try_search,
)
from agent.browser.path_extractor import can_extract, try_extract
from agent.browser.path_vision import can_vision, try_vision
from agent.browser.screenshot_manager import ScreenshotManager, get_or_create_manager

logger = logging.getLogger(__name__)


class BrowserPath(str, Enum):
    EXTRACT = "extract"
    DETERMINISTIC = "deterministic"
    A11Y = "a11y"
    VISION = "vision"
    BLOCKED = "blocked"


PATH_PRIORITY = [
    BrowserPath.EXTRACT,
    BrowserPath.DETERMINISTIC,
    BrowserPath.A11Y,
    BrowserPath.VISION,
    BrowserPath.BLOCKED,
]

PATH_COST_MAP = {
    BrowserPath.EXTRACT: 1,
    BrowserPath.DETERMINISTIC: 3,
    BrowserPath.A11Y: 4,
    BrowserPath.VISION: 5,
    BrowserPath.BLOCKED: 0,
}


class BrowserEngine:
    """Multi-path browser execution engine with automatic path selection."""

    def __init__(
        self,
        session_id: str | None = None,
        headless: bool = True,
    ) -> None:
        self.session_id = session_id or f"be_{int(time.time())}"
        self.headless = headless
        self.screenshot_mgr: ScreenshotManager = get_or_create_manager(self.session_id)
        self.action_logger: ActionLogger = create_action_logger()
        self.selected_path: BrowserPath | None = None
        self.path_results: dict[str, dict[str, Any]] = {}
        self._browser = None
        self._context = None
        self._page = None

    async def _launch_browser(self) -> Any:
        """Launch Playwright browser if not already running."""
        if self._page is not None:
            return self._page

        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
        )
        self._page = await self._context.new_page()
        return self._page

    async def _close_browser(self) -> None:
        """Close the browser if it was launched."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if hasattr(self, "_playwright") and self._playwright:
                await self._playwright.stop()
        except Exception as exc:
            logger.debug("Browser close error (non-fatal): %s", exc)
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None

    def select_path(self, url: str, task_type: str = "") -> BrowserPath:
        """Select the cheapest viable path for a URL/task."""
        scores = {}
        scores[BrowserPath.EXTRACT] = can_extract(url, task_type)
        scores[BrowserPath.DETERMINISTIC] = can_deterministic(url, task_type)
        scores[BrowserPath.A11Y] = can_a11y(url, task_type)
        scores[BrowserPath.VISION] = can_vision(url, task_type)

        logger.info("Path scores for %s: extract=%s, det=%s, a11y=%s, vision=%s",
                     url, scores[BrowserPath.EXTRACT], scores[BrowserPath.DETERMINISTIC],
                     scores[BrowserPath.A11Y], scores[BrowserPath.VISION])

        best_path = BrowserPath.EXTRACT
        best_score = 0.0

        for path in PATH_PRIORITY:
            if path == BrowserPath.BLOCKED:
                continue
            score = scores.get(path, 0.0)
            adjusted = score * (1.0 + 0.05 / max(PATH_COST_MAP.get(path, 1), 1))
            if adjusted > best_score:
                best_score = adjusted
                best_path = path

        self.selected_path = best_path
        logger.info("Selected path: %s (score=%.2f)", best_path.value, best_score)
        return best_path

    async def execute_path(
        self,
        path: BrowserPath,
        url: str,
        task_type: str = "",
    ) -> dict[str, Any]:
        """Execute a specific path and return results."""
        page = await self._launch_browser()
        logger.info("Executing path: %s for %s", path.value, url)

        path_start = time.perf_counter()

        if path == BrowserPath.EXTRACT:
            result = await try_extract(url)
        elif path == BrowserPath.DETERMINISTIC:
            result = await try_deterministic(
                url, page, self.screenshot_mgr, self.action_logger,
            )
        elif path == BrowserPath.A11Y:
            result = await try_a11y(
                url, page, self.screenshot_mgr, self.action_logger,
            )
        elif path == BrowserPath.VISION:
            result = await try_vision(
                url, page, self.screenshot_mgr, self.action_logger,
            )
        elif path == BrowserPath.BLOCKED:
            result = await try_detect_blocked(
                url, page, self.screenshot_mgr, self.action_logger,
            )
        else:
            result = {"path": "unknown", "success": False, "error": "Unknown path"}

        path_duration = (time.perf_counter() - path_start) * 1000
        result["duration_ms"] = path_duration
        result["path"] = path.value
        self.path_results[path.value] = result

        if result.get("success"):
            self.action_logger.log_action(
                "path_success",
                target=path.value,
                url=url,
                status="success",
                duration_ms=path_duration,
                metadata={"path": path.value},
            )

        return result


    async def execute(
        self,
        url: str,
        task_type: str = "",
        *,
        force_path: BrowserPath | None = None,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """Execute the best path, with fallback on failure."""
        overall_start = time.perf_counter()

        try:
            if force_path:
                paths_to_try = [force_path]
            else:
                selected = self.select_path(url, task_type)
                paths_to_try = [selected]

            last_result = None
            recovery_attempts = 0

            for path in paths_to_try:
                if not force_path and last_result and last_result.get("success"):
                    break

                result = await self.execute_path(path, url, task_type)
                last_result = result

                if result.get("success"):
                    break

                if not force_path:
                    current_idx = PATH_PRIORITY.index(path) if path in PATH_PRIORITY else 0
                    if current_idx + 1 < len(PATH_PRIORITY):
                        next_path = PATH_PRIORITY[current_idx + 1]
                        if next_path != BrowserPath.BLOCKED:
                            logger.info(
                                "Path %s failed, falling back to %s",
                                path.value, next_path.value,
                            )
                            self.action_logger.log_recovery(
                                f"fallback_{path.value}_to_{next_path.value}",
                                target=url,
                                url=url,
                                recovery_path=next_path.value,
                            )
                            recovery_attempts += 1
                            paths_to_try.append(next_path)

            if not last_result:
                last_result = {"path": "none", "success": False, "error": "No path executed"}

            overall_duration = (time.perf_counter() - overall_start) * 1000
            last_result["total_duration_ms"] = overall_duration
            last_result["recovery_attempts"] = recovery_attempts
            last_result["paths_tried"] = [p.value for p in paths_to_try]

            if recovery_attempts > 0 and last_result.get("success"):
                last_result["recovered"] = True
                self.action_logger.log_action(
                    "recovery_success",
                    target=url,
                    url=url,
                    status="success",
                    metadata={"recovery_attempts": recovery_attempts},
                )

            return last_result
        finally:
            pass

    async def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Perform a search on the current page."""
        page = await self._launch_browser()
        return await try_search(
            page, query,
            screenshot_mgr=self.screenshot_mgr,
            action_logger=self.action_logger,
            **kwargs,
        )

    async def click_sort(self, sort_text: str = "Likes") -> dict[str, Any]:
        """Click a sort option."""
        page = await self._launch_browser()
        return await try_click_sort(
            page, sort_text,
            screenshot_mgr=self.screenshot_mgr,
            action_logger=self.action_logger,
        )

    async def click_filter(self, filter_text: str) -> dict[str, Any]:
        """Click a filter option."""
        page = await self._launch_browser()
        return await try_click_filter(
            page, filter_text,
            screenshot_mgr=self.screenshot_mgr,
            action_logger=self.action_logger,
        )

    async def open_detail(self, index: int = 0) -> dict[str, Any]:
        """Open a detail page."""
        page = await self._launch_browser()
        return await try_open_detail(
            page, index=index,
            screenshot_mgr=self.screenshot_mgr,
            action_logger=self.action_logger,
        )

    async def paginate(self, page_num: int = 2) -> dict[str, Any]:
        """Go to next page."""
        page = await self._launch_browser()
        return await try_paginate(
            page, page_num=page_num,
            screenshot_mgr=self.screenshot_mgr,
            action_logger=self.action_logger,
        )

    async def extract_content(self, url: str) -> dict[str, Any]:
        """Full extraction pipeline."""
        result = await self.execute(url)
        return result

    def get_report_data(self) -> dict[str, Any]:
        """Get all data for replay report."""
        return {
            "session_id": self.session_id,
            "selected_path": self.selected_path.value if self.selected_path else None,
            "path_results": self.path_results,
            "actions": self.action_logger.get_report_data(),
            "screenshots": self.screenshot_mgr.get_report_data(),
            "action_count": self.action_logger.get_action_count(),
            "action_types": self.action_logger.get_browser_action_types(),
        }

    async def cleanup(self) -> None:
        """Clean up browser resources."""
        await self._close_browser()


async def create_browser_engine(
    session_id: str | None = None,
    headless: bool = True,
) -> BrowserEngine:
    """Create and return a BrowserEngine instance."""
    return BrowserEngine(session_id=session_id, headless=headless)
