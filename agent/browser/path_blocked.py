"""Path 5: Blocked — Detection of CAPTCHA, auth walls, Cloudflare, anti-bot systems.

Used when all other paths fail."""

from __future__ import annotations

import logging
import re
from typing import Any

from agent.browser.action_logger import ActionLogger
from agent.browser.screenshot_manager import ScreenshotManager

logger = logging.getLogger(__name__)

# Patterns that indicate blocking/anti-bot
BLOCKED_PATTERNS = {
    "captcha": [
        r"captcha",
        r"recaptcha",
        r"hcaptcha",
        r"verify\s+you\'?re\s+human",
        r"are\s+you\s+a\s+robot",
        r"i\'?m\s+not\s+a\s+robot",
        r"turnstile",
        r"challenge",
    ],
    "cloudflare": [
        r"cloudflare",
        r"checking\s+browser",
        r"just\s+a\s+moment",
        r"attention\s+required",
    ],
    "auth_wall": [
        r"sign\s+in",
        r"log\s+in",
        r"login",
        r"signup",
        r"create\s+account",
        r"authentication\s+required",
        r"access\s+denied",
        r"403\s+forbidden",
        r"401\s+unauthorized",
    ],
    "rate_limit": [
        r"too\s+many\s+requests",
        r"rate\s+limited",
        r"429",
        r"try\s+again\s+later",
    ],
    "blocked": [
        r"access\s+denied",
        r"blocked",
        r"403",
        r"forbidden",
        r"your\s+request\s+has\s+been\s+blocked",
        r"security\s+check",
    ],
}


async def try_detect_blocked(
    url: str,
    page: Any,
    screenshot_mgr: ScreenshotManager | None = None,
    action_logger: ActionLogger | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Detect if a page is blocked by anti-bot measures.

    Returns detection results. If blocked, provides reason and suggested recovery.
    """
    result: dict[str, Any] = {
        "path": "blocked",
        "url": url,
        "success": False,
        "is_blocked": False,
        "block_type": None,
        "reason": None,
        "content": "",
        "title": "",
        "error": None,
    }

    try:
        if action_logger:
            action_logger.log_navigate(url)

        await page.goto(url, timeout=int(timeout * 1000), wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)

        title = await page.title()
        content = await page.content()
        text = await page.inner_text("body")

        result["title"] = title
        result["content"] = text[:5000]

        # Check for blocking patterns
        for block_type, patterns in BLOCKED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result["is_blocked"] = True
                    result["block_type"] = block_type
                    result["reason"] = f"Detected {block_type}: matched pattern '{pattern}'"
                    result["success"] = False
                    if action_logger:
                        action_logger.log_action(
                            "blocked_detected",
                            target=url,
                            url=url,
                            status="blocked",
                            error=f"Blocked by {block_type}",
                        )
                    if screenshot_mgr:
                        await screenshot_mgr.capture_failure(page, f"blocked_{block_type}")
                    logger.warning("Path BLOCKED: %s detected for %s", block_type, url)
                    return result

        # Check HTTP status via response
        try:
            response = await page.wait_for_url("**", timeout=1000)
            if response:
                status = response.status
                if status in (403, 401, 429):
                    result["is_blocked"] = True
                    result["block_type"] = "http_blocked"
                    result["reason"] = f"HTTP {status} response"
                    result["success"] = False
                    if screenshot_mgr:
                        await screenshot_mgr.capture_failure(page, f"http_{status}")
                    logger.warning("Path BLOCKED: HTTP %d for %s", status, url)
                    return result
        except Exception:
            pass

        # Not blocked — page loaded successfully
        result["success"] = True
        result["is_blocked"] = False
        result["content"] = text[:8000]
        logger.info("Path BLOCKED check: passed for %s (not blocked)", url)
        return result

    except Exception as exc:
        logger.warning("Path BLOCKED detection failed for %s: %s", url, exc)
        result["error"] = str(exc)
        result["is_blocked"] = True
        result["block_type"] = "unknown"
        result["reason"] = f"Error during detection: {exc}"
        return result


def suggest_recovery(result: dict[str, Any]) -> dict[str, Any]:
    """Suggest recovery strategy based on block type."""
    block_type = result.get("block_type")

    recovery_map = {
        "captcha": {
            "strategy": "retry_with_vision",
            "message": "CAPTCHA detected. Vision path may help.",
        },
        "cloudflare": {
            "strategy": "retry_with_longer_timeout",
            "message": "Cloudflare challenge. Retry with longer wait.",
        },
        "auth_wall": {
            "strategy": "skip_requires_auth",
            "message": "Authentication required. Cannot access without credentials.",
        },
        "rate_limit": {
            "strategy": "retry_with_backoff",
            "message": "Rate limited. Retry after backoff.",
        },
        "http_blocked": {
            "strategy": "retry_with_different_approach",
            "message": "HTTP blocking detected. Try alternative approach.",
        },
    }

    return recovery_map.get(block_type, {
        "strategy": "unknown",
        "message": "Unknown block type. Manual intervention may be required.",
    })
