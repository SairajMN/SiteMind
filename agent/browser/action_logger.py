"""Action logger — logs every browser action with timestamps, screenshots, and results."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class ActionLogger:
    """Logs every browser action with full provenance for replay."""

    def __init__(self) -> None:
        self.actions: list[dict[str, Any]] = []
        self._step_counter = 0

    def _next_step(self) -> int:
        self._step_counter += 1
        return self._step_counter

    def log_action(
        self,
        action: str,
        target: str = "",
        url: str = "",
        status: str = "success",
        result: Any = None,
        screenshot_ref: str = "",
        selector: str = "",
        error: str | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log a browser action with full context."""
        step = self._next_step()
        entry: dict[str, Any] = {
            "step": step,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "unix_ms": int(time.time() * 1000),
            "action": action,
            "target": target,
            "url": url,
            "status": status,
            "selector": selector,
            "error": error,
            "duration_ms": duration_ms,
        }
        if screenshot_ref:
            entry["screenshot"] = screenshot_ref
        if result is not None:
            entry["result"] = result
        if metadata:
            entry["metadata"] = metadata

        self.actions.append(entry)
        logger.info("[Action %02d] %s → %s [%s]", step, action, target or url, status)
        return entry

    def log_search(self, query: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("search", target=query, url=url, **kwargs)

    def log_click(self, target: str, url: str = "", selector: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("click", target=target, url=url, selector=selector, **kwargs)

    def log_sort(self, field: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("sort", target=field, url=url, **kwargs)

    def log_filter(self, filter_name: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("filter", target=filter_name, url=url, **kwargs)

    def log_paginate(self, page_num: int, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("paginate", target=str(page_num), url=url, **kwargs)

    def log_expand(self, target: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("expand", target=target, url=url, **kwargs)

    def log_tab_switch(self, tab_name: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("tab_switch", target=tab_name, url=url, **kwargs)

    def log_open_detail(self, target: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("open_detail", target=target, url=url, **kwargs)

    def log_form_submit(self, form_data: str, url: str = "", **kwargs: Any) -> dict[str, Any]:
        return self.log_action("form_submit", target=form_data, url=url, **kwargs)

    def log_navigate(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return self.log_action("navigate", target=url, url=url, **kwargs)

    def log_failure(
        self,
        action: str,
        target: str,
        url: str = "",
        error: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        return self.log_action(action, target=target, url=url, status="failure", error=error, **kwargs)

    def log_recovery(
        self,
        action: str,
        target: str,
        url: str = "",
        recovery_path: str = "",
        **kwargs: Any,
    ) -> dict[str, Any]:
        entry = self.log_action(
            action,
            target=target,
            url=url,
            status="recovery",
            metadata={"recovery_path": recovery_path},
            **kwargs,
        )
        return entry

    def get_action_count(self) -> int:
        """Get total number of logged actions."""
        return len(self.actions)

    def get_browser_action_types(self) -> list[str]:
        """Get distinct action types performed."""
        return list({a["action"] for a in self.actions})

    def get_report_data(self) -> list[dict[str, Any]]:
        """Get action data for replay report."""
        return list(self.actions)


def create_action_logger() -> ActionLogger:
    """Create a new ActionLogger instance."""
    return ActionLogger()
