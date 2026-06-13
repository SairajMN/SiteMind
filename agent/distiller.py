"""Distiller — converts raw browser output into normalized comparison objects.

Extracts structured fields: name, source_url, score, price, likes, downloads,
rating, description, features. Only populates fields supported by evidence.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class Distiller:
    """Converts raw browser/page content into normalized comparison items."""

    SUPPORTED_DOMAINS = {
        "huggingface": "huggingface",
        "github": "github",
        "pypi": "pypi",
        "producthunt": "producthunt",
        "amazon": "amazon",
    }

    def __init__(self, query: str, url: str = "") -> None:
        self.query = query
        self.url = url
        self.domain = self._detect_domain(url)

    def _detect_domain(self, url: str) -> str | None:
        for domain_key, domain_value in self.SUPPORTED_DOMAINS.items():
            if domain_key in url.lower():
                return domain_value
        return None

    async def distill(
        self,
        browser_result: dict[str, Any],
        min_items: int = 3,
    ) -> dict[str, Any]:
        """Distill raw browser output into normalized comparison items."""
        result: dict[str, Any] = {
            "items": [],
            "total_extracted": 0,
            "domain": self.domain,
            "distillation_method": "heuristic",
            "raw_content_length": 0,
            "confidence": 0.0,
            "missing_fields": [],
        }

        content = browser_result.get("content", "")
        extracted_items = browser_result.get("items", [])
        listings = browser_result.get("listings", [])
        tables = browser_result.get("tables", [])
        title = browser_result.get("title", "")

        result["raw_content_length"] = len(content)
        result["page_title"] = title

        if extracted_items:
            items = self._normalize_items(extracted_items, browser_result.get("url", self.url))
            if items:
                result["items"] = items
                result["distillation_method"] = "extracted_items"

        if not result["items"] and listings:
            items = self._parse_listings(listings, browser_result.get("url", self.url))
            if items:
                result["items"] = items
                result["distillation_method"] = "listings"

        if not result["items"] and tables:
            items = self._parse_tables(tables, browser_result.get("url", self.url))
            if items:
                result["items"] = items
                result["distillation_method"] = "tables"

        if not result["items"] and content:
            items = self._parse_text_content(content, browser_result.get("url", self.url))
            if items:
                result["items"] = items
                result["distillation_method"] = "text_parsing"

        result["items"] = self._deduplicate_items(result["items"])
        result["total_extracted"] = len(result["items"])

        if result["items"]:
            self._validate_fields(result)
            result["confidence"] = self._calculate_confidence(result, min_items)

        result["items"] = result["items"][:10]

        logger.info(
            "Distilled %d items from %s (method=%s, confidence=%.2f)",
            result["total_extracted"],
            self.url or self.query,
            result["distillation_method"],
            result["confidence"],
        )

        return result

    def _normalize_items(self, raw_items: list[dict[str, Any]], base_url: str) -> list[dict[str, Any]]:
        items = []
        for raw in raw_items:
            item = {
                "name": raw.get("name", ""),
                "source_url": self._resolve_url(raw.get("href", ""), base_url),
                "score": raw.get("score", ""),
                "price": raw.get("price", ""),
                "likes": raw.get("likes", ""),
                "downloads": raw.get("downloads", ""),
                "rating": raw.get("rating", ""),
                "description": raw.get("description", ""),
                "features": raw.get("features", []),
            }
            if item["name"]:
                items.append(item)
        return items

    def _parse_listings(self, listings: list[dict[str, Any]], base_url: str) -> list[dict[str, Any]]:
        items = []
        for listing in listings:
            text = listing.get("text", "")
            href = listing.get("href", "")
            if not text or len(text) < 5:
                continue
            item = {
                "name": text[:100].split("\n")[0].strip(),
                "source_url": self._resolve_url(href, base_url),
                "description": text[:200],
            }
            likes = re.search(r"(\d+[kKmMbB]?)\s*(likes|❤|⭐)", text, re.I)
            if likes:
                item["likes"] = likes.group(1)
            downloads = re.search(r"(\d+[kKmMbB]?)\s*(downloads|installs)", text, re.I)
            if downloads:
                item["downloads"] = downloads.group(1)
            price = re.search(r"(\$[\d,]+\.?\d*|\u20ac[\d,]+\.?\d*|\u00a3[\d,]+\.?\d*)", text)
            if price:
                item["price"] = price.group(1)
            if item.get("name"):
                items.append(item)
        return items

    def _parse_tables(self, tables: list[dict[str, Any]], base_url: str) -> list[dict[str, Any]]:
        items = []
        for table in tables:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            for row in rows:
                item = {"name": "", "source_url": base_url, "score": "", "price": "",
                        "likes": "", "downloads": "", "rating": "", "description": "", "features": []}
                for i, cell in enumerate(row):
                    cell = cell.strip()
                    if i == 0:
                        item["name"] = cell
                    elif i < len(headers):
                        h = headers[i].lower() if headers else ""
                        if any(k in h for k in ("name", "model", "product", "title")):
                            item["name"] = cell
                        elif any(k in h for k in ("like", "\u2764", "favorite")):
                            item["likes"] = cell
                        elif any(k in h for k in ("download", "install")):
                            item["downloads"] = cell
                        elif any(k in h for k in ("price", "cost", "$")):
                            item["price"] = cell
                        elif any(k in h for k in ("rating", "score", "star")):
                            item["rating"] = cell
                        elif not item["description"]:
                            item["description"] = cell[:200]
                    elif not item["description"]:
                        item["description"] = cell[:200]
                if item.get("name"):
                    items.append(item)
        return items

    def _parse_text_content(self, content: str, base_url: str) -> list[dict[str, Any]]:
        items = []
        lines = content.split("\n")
        current_item = None
        
        # Strict skip words - only skip unambiguous navigation items
        skip_words = {"models", "datasets", "spaces", "docs", "pricing", "blog",
                       "community", "solutions", "enterprise", "about", "tasks",
                       "libraries", "languages", "licenses", "apps"}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # STRICT item detection: only lines with org/name pattern or model names
            is_model_name = bool(re.match(r"^[a-zA-Z0-9_\.\-]+/[a-zA-Z0-9_\.\-]+$", line))
            
            # Only accept as item name if it looks like an actual model/product name
            is_item_name = is_model_name
            
            if is_item_name:
                if current_item and current_item.get("name"):
                    items.append(current_item)
                current_item = {"name": line, "source_url": base_url, "score": "", "price": "",
                                "likes": "", "downloads": "", "rating": "", "description": "", "features": []}
                continue
            
            if current_item:
                line_lower = line.lower()
                
                # Look for inline model metadata: "5.59M  •  13.4k" 
                meta = re.search(r"(\d+[\.\,]?\d*[kKmMbB]?)\s*•\s*(\d+[\.\,]?\d*[kKmMbB]?)", line)
                if meta:
                    if not current_item["likes"]:
                        current_item["likes"] = meta.group(1)
                    if not current_item["downloads"]:
                        current_item["downloads"] = meta.group(2)
                    continue
                
                # Single number with context
                num_match = re.search(r"(\d+[\.\,]?\d*[kKmMbB]?)", line)
                if num_match:
                    val = num_match.group(1)
                    if any(w in line_lower for w in ["like", "❤", "⭐", "favorite"]):
                        if not current_item["likes"]:
                            current_item["likes"] = val
                    elif any(w in line_lower for w in ["download", "install", "use this"]):
                        if not current_item["downloads"]:
                            current_item["downloads"] = val
                    elif any(w in line_lower for w in ["updated", "update", "modified"]):
                        # Skip date lines
                        pass
                    else:
                        # First number after model name is often likes
                        if not current_item["likes"] and not re.match(r"^\d+[BkKmM]?$", val):
                            current_item["likes"] = val
                        elif not current_item["downloads"]:
                            current_item["downloads"] = val
                
                # Description (multi-line text after numbers)
                if not re.search(r"\d", line) and line_lower not in ("text generation", "text-to-image", "image-to-text"):
                    if current_item.get("likes") or current_item.get("downloads"):
                        if not current_item["description"]:
                            current_item["description"] = line[:200]
        
        if current_item and current_item.get("name"):
            items.append(current_item)
        
        # Filter: only keep items that have meaningful names (not single words)
        items = [it for it in items if "/" in it.get("name", "") or len(it.get("name", "")) > 10]
        
        return items

    def _resolve_url(self, href: str, base_url: str) -> str:
        if not href:
            return base_url
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            match = re.match(r"(https?://[^/]+)", base_url)
            if match:
                return match.group(1) + href
        return base_url.rstrip("/") + "/" + href.lstrip("/")

    def _deduplicate_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        unique = []
        for item in items:
            name = item.get("name", "").lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(item)
        return unique

    def _validate_fields(self, result: dict[str, Any]) -> None:
        all_fields = {"name", "source_url", "score", "price", "likes", "downloads", "rating", "description"}
        present = {f: 0 for f in all_fields}
        for item in result["items"]:
            for field in all_fields:
                val = item.get(field)
                if val and str(val).strip():
                    present[field] += 1
        total = len(result["items"])
        result["missing_fields"] = [f for f, c in present.items() if c < total]
        result["field_coverage"] = {f: f"{c}/{total}" for f, c in present.items()}

    def _calculate_confidence(self, result: dict[str, Any], min_items: int) -> float:
        total = len(result["items"])
        if total == 0:
            return 0.0
        count_score = min(total / max(min_items, 1), 1.0) * 0.4
        field_count = sum(1 for item in result["items"]
                          if item.get("name") and (item.get("likes") or item.get("downloads") or item.get("rating")))
        field_score = (field_count / total) * 0.4
        method_scores = {"extracted_items": 1.0, "listings": 0.8, "tables": 0.7, "text_parsing": 0.5, "heuristic": 0.3}
        method_score = method_scores.get(result.get("distillation_method", "heuristic"), 0.3) * 0.2
        return round(count_score + field_score + method_score, 2)


async def distill_content(
    browser_result: dict[str, Any],
    query: str,
    url: str = "",
    min_items: int = 3,
) -> dict[str, Any]:
    distiller = Distiller(query, url)
    return await distiller.distill(browser_result, min_items)
