from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

import bleach

from app.core.config import get_settings

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)

_BLOCKED_SCHEMES = frozenset({"file", "ftp", "gopher", "data", "javascript"})


class SecurityError(ValueError):
    """Raised when a URL or crawl parameter fails safety checks."""


def _host_to_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    host = host.strip().lower().rstrip(".")
    if host in ("localhost", "127.0.0.1", "::1"):
        return ipaddress.ip_address("127.0.0.1")
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def is_private_or_reserved_host(host: str) -> bool:
    settings = get_settings()
    if settings.allow_localhost_targets and host.lower() in (
        "localhost",
        "127.0.0.1",
        "::1",
    ):
        return False
    addr = _host_to_ip(host)
    if addr is None:
        return False
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
        return True
    for net in _PRIVATE_NETWORKS:
        if addr in net:
            return True
    return False


def validate_target_url(url: str) -> str:
    """Validate URL for SSRF-safe crawling (http/https only, no private IPs)."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise SecurityError("URL must use http or https")
    if parsed.scheme in _BLOCKED_SCHEMES:
        raise SecurityError("URL scheme is not allowed")
    if not parsed.netloc or not parsed.hostname:
        raise SecurityError("URL must include a valid host")
    host = parsed.hostname
    if is_private_or_reserved_host(host):
        raise SecurityError("Target host resolves to a private or local address")
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized.rstrip("/") if normalized.endswith("//") else normalized


def extract_domain(url: str) -> str:
    host = urlparse(url).hostname
    if not host:
        raise SecurityError("Could not extract domain from URL")
    return host.lower()


def same_domain(url: str, root_url: str) -> bool:
    return extract_domain(url) == extract_domain(root_url)


def clamp_depth(requested: int, *, maximum: int | None = None) -> int:
    settings = get_settings()
    cap = maximum if maximum is not None else settings.crawl_max_depth
    if requested < 1:
        return 1
    return min(requested, cap)


def clamp_page_budget(requested: int, *, maximum: int | None = None) -> int:
    settings = get_settings()
    cap = maximum if maximum is not None else settings.crawl_max_page_budget
    if requested < 1:
        return settings.crawl_default_page_budget
    return min(requested, cap)


def sanitize_html(raw: str, *, max_length: int = 500_000) -> str:
    if len(raw) > max_length:
        raw = raw[:max_length]
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        "p",
        "div",
        "span",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "article",
        "section",
        "header",
        "footer",
        "nav",
        "main",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
        "td",
        "th",
        "thead",
        "tbody",
        "pre",
        "code",
    ]
    return bleach.clean(
        raw,
        tags=allowed_tags,
        attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES,
        strip=True,
    )


_SCOPE_PATTERN = re.compile(r"^[a-z_]+$")


def validate_scope_policy(policy: str) -> str:
    policy = policy.strip().lower()
    if policy not in ("same_domain",):
        raise SecurityError(f"Unsupported scope policy: {policy}")
    if not _SCOPE_PATTERN.match(policy):
        raise SecurityError("Invalid scope policy format")
    return policy
