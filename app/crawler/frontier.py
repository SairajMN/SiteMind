from __future__ import annotations

from collections import deque
from urllib.parse import urlparse


class CrawlFrontier:
    def __init__(self, root_url: str, max_depth: int, page_budget: int) -> None:
        self.root_url = self._normalize(root_url)
        self.max_depth = max_depth
        self.page_budget = page_budget
        self._queue: deque[tuple[str, int]] = deque([(root_url, 0)])
        self._seen: set[str] = {self.root_url}

    @staticmethod
    def _normalize(url: str) -> str:
        return url.split("#")[0].rstrip("/") or url

    def add_links(self, source_url: str, links: list[str], current_depth: int) -> None:
        if current_depth >= self.max_depth:
            return
        for link in links:
            normalized = self._normalize(link)
            if normalized in self._seen:
                continue
            if len(self._seen) >= self.page_budget:
                return
            self._seen.add(normalized)
            self._queue.append((link, current_depth + 1))

    def pop(self) -> tuple[str, int] | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def is_seen(self, url: str) -> bool:
        return self._normalize(url) in self._seen

    @property
    def discovered_count(self) -> int:
        return len(self._seen)
