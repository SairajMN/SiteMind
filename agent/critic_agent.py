"""Critic Agent — validates comparison quality with 6 checks.

Checks:
1. Required item count met
2. Fields complete (non-empty)
3. URLs valid (evidence exists)
4. Evidence exists for each claim
5. Comparison quality sufficient
6. Browser actions >= 3

If any check fails, critic_status = FAILED with detailed reasons."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class CriticAgent:
    """Validates comparison output quality and triggers recovery if needed."""

    def __init__(self, query: str, min_items: int = 3, min_actions: int = 3) -> None:
        self.query = query
        self.min_items = min_items
        self.min_actions = min_actions
        self.checks: dict[str, dict[str, Any]] = {}
        self.status: str = "PASSED"

    async def evaluate(
        self,
        distiller_output: dict[str, Any],
        browser_actions: list[dict[str, Any]],
        browser_report: dict[str, Any],
    ) -> dict[str, Any]:
        """Run all 6 validation checks."""
        self.checks = {}
        await self._check_item_count(distiller_output)
        await self._check_fields_complete(distiller_output)
        await self._check_urls_valid(distiller_output)
        await self._check_evidence_exists(distiller_output)
        await self._check_comparison_quality(distiller_output)
        await self._check_browser_actions(browser_actions)

        all_passed = all(check["passed"] for check in self.checks.values())
        self.status = "PASSED" if all_passed else "FAILED"

        result = {
            "status": self.status,
            "checks": self.checks,
            "passed_count": sum(1 for c in self.checks.values() if c["passed"]),
            "failed_count": sum(1 for c in self.checks.values() if not c["passed"]),
            "total_checks": len(self.checks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recovery_action": self._suggest_recovery() if not all_passed else None,
        }

        logger.info("Critic: %s (%d/%d passed)", self.status, result["passed_count"], result["total_checks"])
        return result

    async def _check_item_count(self, distiller_output: dict[str, Any]) -> None:
        items = distiller_output.get("items", [])
        count = len(items)
        passed = count >= self.min_items
        self.checks["item_count"] = {
            "name": "Required item count met",
            "passed": passed,
            "expected": f">= {self.min_items}",
            "actual": count,
            "detail": f"Found {count} items, needed {self.min_items}" if not passed else f"Found {count} items",
        }

    async def _check_fields_complete(self, distiller_output: dict[str, Any]) -> None:
        items = distiller_output.get("items", [])
        if not items:
            self.checks["fields_complete"] = {"name": "Fields complete", "passed": False,
                "expected": "Non-empty fields", "actual": "No items", "detail": "No items to check"}
            return
        required_fields = ["name"]
        valuable_fields = ["likes", "downloads", "rating", "price"]
        missing = []
        for item in items:
            for field in required_fields:
                if not item.get(field):
                    missing.append(f"{field} missing in '{item.get('name', 'unknown')}'")
        valuable_count = sum(1 for item in items if any(item.get(f) for f in valuable_fields))
        passed = len(missing) == 0 and valuable_count >= max(1, len(items) // 2)
        self.checks["fields_complete"] = {
            "name": "Fields complete (non-empty)", "passed": passed,
            "expected": "Required fields non-empty, valuable fields present",
            "actual": f"{len(missing)} issues, {valuable_count}/{len(items)} items have valuable fields",
            "detail": "; ".join(missing) if missing else "All required fields present",
        }

    async def _check_urls_valid(self, distiller_output: dict[str, Any]) -> None:
        items = distiller_output.get("items", [])
        if not items:
            self.checks["urls_valid"] = {"name": "URLs valid", "passed": False,
                "expected": "Valid URLs", "actual": "No items", "detail": "No items to check"}
            return
        url_pattern = re.compile(r"https?://[^\s/$.?#].[^\s]*")
        invalid = []
        for item in items:
            url = item.get("source_url", "")
            if url and not url_pattern.match(url):
                invalid.append(f"Invalid URL: {url}")
        passed = len(invalid) == 0
        self.checks["urls_valid"] = {
            "name": "URLs valid", "passed": passed,
            "expected": "All URLs valid", "actual": f"{len(invalid)} invalid URLs",
            "detail": "; ".join(invalid) if invalid else "All URLs valid",
        }

    async def _check_evidence_exists(self, distiller_output: dict[str, Any]) -> None:
        items = distiller_output.get("items", [])
        if not items:
            self.checks["evidence_exists"] = {"name": "Evidence exists", "passed": False,
                "expected": "Evidence for each item", "actual": "No items", "detail": "No items"}
            return
        no_evidence = []
        for item in items:
            url = item.get("source_url", "")
            name = item.get("name", "unknown")
            if not url or url == distiller_output.get("domain", ""):
                no_evidence.append(f"No source URL for '{name}'")
        passed = len(no_evidence) == 0
        self.checks["evidence_exists"] = {
            "name": "Evidence exists for each claim", "passed": passed,
            "expected": "Each item has a source URL",
            "actual": f"{len(no_evidence)} items without evidence",
            "detail": "; ".join(no_evidence) if no_evidence else "All items have evidence URLs",
        }

    async def _check_comparison_quality(self, distiller_output: dict[str, Any]) -> None:
        items = distiller_output.get("items", [])
        confidence = distiller_output.get("confidence", 0.0)
        if not items:
            self.checks["comparison_quality"] = {"name": "Comparison quality sufficient", "passed": False,
                "expected": "Meaningful data", "actual": "No items", "detail": "Cannot compare zero items"}
            return
        has_ranking_metric = any(
            item.get("likes") or item.get("downloads") or item.get("rating") or item.get("price")
            for item in items)
        meaningful_names = all(len(item.get("name", "")) > 3 for item in items)
        sufficient_confidence = confidence >= 0.3
        quality_issues = []
        if not has_ranking_metric:
            quality_issues.append("No ranking metrics (likes/downloads/rating) found")
        if not meaningful_names:
            quality_issues.append("Item names are too short or missing")
        if not sufficient_confidence:
            quality_issues.append(f"Confidence too low ({confidence:.2f})")
        passed = has_ranking_metric and meaningful_names and sufficient_confidence
        self.checks["comparison_quality"] = {
            "name": "Comparison quality sufficient", "passed": passed,
            "expected": "Ranking metrics + names + confidence >= 0.3",
            "actual": f"metrics={'yes' if has_ranking_metric else 'no'}, names={'ok' if meaningful_names else 'short'}, confidence={confidence:.2f}",
            "detail": "; ".join(quality_issues) if quality_issues else "Good comparison quality",
        }

    async def _check_browser_actions(self, browser_actions: list[dict[str, Any]]) -> None:
        if not browser_actions:
            self.checks["browser_actions"] = {"name": "Browser actions >= 3", "passed": False,
                "expected": f">= {self.min_actions} browser actions", "actual": "0 actions",
                "detail": "No browser actions recorded"}
            return
        meaningful_actions = [
            a for a in browser_actions
            if a.get("action") not in ("path_success", "recovery_success", "page_loaded")]
        count = len(meaningful_actions)
        passed = count >= self.min_actions
        action_types = list({a.get("action", "unknown") for a in meaningful_actions})
        self.checks["browser_actions"] = {
            "name": "Browser actions >= 3", "passed": passed,
            "expected": f">= {self.min_actions} browser actions",
            "actual": f"{count} actions",
            "detail": f"Actions: {', '.join(action_types)}" if action_types else "No actions",
            "action_types": action_types,
        }

    def _suggest_recovery(self) -> str:
        failed = [name for name, check in self.checks.items() if not check["passed"]]
        recovery_map = {
            "item_count": "RETRY with more extraction attempts or different URL",
            "fields_complete": "RETRY with enhanced parsing or different selectors",
            "urls_valid": "FIX URL resolution in distiller",
            "evidence_exists": "RETRY with full URL capture in browser engine",
            "comparison_quality": "RETRY with different sorting or data source",
            "browser_actions": "RETRY with more browser interactions",
        }
        suggestions = [recovery_map.get(f, "RETRY") for f in failed]
        return "; ".join(suggestions)


async def evaluate_comparison(
    distiller_output: dict[str, Any],
    browser_actions: list[dict[str, Any]],
    browser_report: dict[str, Any],
    query: str = "",
    min_items: int = 3,
    min_actions: int = 3,
) -> dict[str, Any]:
    critic = CriticAgent(query, min_items, min_actions)
    return await critic.evaluate(distiller_output, browser_actions, browser_report)
