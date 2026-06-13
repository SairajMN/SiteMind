"""Screenshot pipeline — captures, stores, and manages screenshots for replay."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path(__file__).resolve().parents[2] / "screenshots"


class ScreenshotManager:
    """Manages screenshot capture pipeline with before/after/failure states."""

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.screenshot_dir = SCREENSHOT_DIR / self.session_id
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._step_counter = 0
        self._screenshots: list[dict[str, Any]] = []

    @property
    def screenshots(self) -> list[dict[str, Any]]:
        return list(self._screenshots)

    def _next_step(self) -> str:
        self._step_counter += 1
        return f"step_{self._step_counter:02d}"

    async def capture(
        self,
        page: Any,
        label: str = "",
        kind: str = "state",
    ) -> dict[str, Any]:
        """Capture a screenshot of the current page state."""
        step = self._next_step()
        filename = f"{step}_{kind}.png"
        filepath = self.screenshot_dir / filename

        try:
            screenshot_bytes = await page.screenshot(full_page=False)
            filepath.write_bytes(screenshot_bytes)
            url = page.url
            title = await page.title()

            entry = {
                "step": self._step_counter,
                "filename": filename,
                "relative_path": f"screenshots/{self.session_id}/{filename}",
                "filepath": str(filepath),
                "url": url,
                "title": title or "",
                "label": label,
                "kind": kind,
                "timestamp": datetime.utcnow().isoformat(),
                "size_bytes": len(screenshot_bytes),
            }
            self._screenshots.append(entry)
            logger.debug("Screenshot %s (%s): %s", filename, kind, url)
            return entry
        except Exception as exc:
            logger.warning("Screenshot capture failed: %s", exc)
            return {
                "step": self._step_counter,
                "filename": filename,
                "relative_path": "",
                "url": "",
                "title": "",
                "label": label,
                "kind": kind,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(exc),
            }

    async def capture_before(self, page: Any, label: str = "") -> dict[str, Any]:
        """Capture screenshot before an interaction."""
        return await self.capture(page, label=label, kind="before")

    async def capture_after(self, page: Any, label: str = "") -> dict[str, Any]:
        """Capture screenshot after an interaction."""
        return await self.capture(page, label=label, kind="after")

    async def capture_failure(self, page: Any, label: str = "") -> dict[str, Any]:
        """Capture screenshot on failure."""
        return await self.capture(page, label=label, kind="failure")

    async def capture_recovery(self, page: Any, label: str = "") -> dict[str, Any]:
        """Capture screenshot on recovery."""
        return await self.capture(page, label=label, kind="recovery")

    def get_screenshots_for_step(self, step: int) -> list[dict[str, Any]]:
        """Get all screenshots for a given step number."""
        return [s for s in self._screenshots if s["step"] == step]

    def get_report_data(self) -> list[dict[str, Any]]:
        """Get screenshot data for replay report."""
        return [
            {
                "step": s["step"],
                "filename": s["filename"],
                "relative_path": s["relative_path"],
                "url": s["url"],
                "title": s["title"],
                "label": s["label"],
                "kind": s["kind"],
                "timestamp": s["timestamp"],
            }
            for s in self._screenshots
        ]


def get_or_create_manager(session_id: str | None = None) -> ScreenshotManager:
    """Get or create a ScreenshotManager instance."""
    return ScreenshotManager(session_id=session_id)
