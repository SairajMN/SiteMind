"""Skill catalog — registry of all browser skills with capabilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillCapability:
    """Describes what a skill can do."""
    skill_name: str
    description: str
    supported_domains: list[str] = field(default_factory=list)
    required_browser: bool = True
    min_actions: int = 3
    path_preference: str = "deterministic"
    comparison_types: list[str] = field(default_factory=lambda: [
        "products", "saas", "ai_models", "repositories",
        "apis", "courses", "cloud_services", "training_institutes",
    ])


# Built-in skill catalog
SKILL_CATALOG: dict[str, SkillCapability] = {
    "browser_comparison": SkillCapability(
        skill_name="browser_comparison",
        description="Compare items across websites using real browser interactions",
        supported_domains=[
            "huggingface.co", "github.com", "pypi.org", "producthunt.com",
            "g2.com", "capterra.com", "amazon.com", "flipkart.com",
        ],
        required_browser=True,
        min_actions=3,
        path_preference="deterministic",
        comparison_types=[
            "products", "saas", "ai_models", "repositories",
            "apis", "courses", "cloud_services", "training_institutes",
        ],
    ),
}


def get_skill(name: str) -> SkillCapability | None:
    """Get a skill by name."""
    return SKILL_CATALOG.get(name)


def find_skill_for_query(query: str, url: str = "") -> SkillCapability | None:
    """Find best matching skill for a query and URL."""
    query_lower = query.lower()

    comparison_keywords = [
        "compare", "comparison", "vs", "versus", "top", "best",
        "rank", "ranking", "sorted", "sort",
    ]

    is_comparison = any(kw in query_lower for kw in comparison_keywords)

    if is_comparison:
        return SKILL_CATALOG["browser_comparison"]

    return SKILL_CATALOG.get("browser_comparison")


def list_skills() -> list[dict[str, Any]]:
    """List all available skills with metadata."""
    return [
        {
            "name": s.skill_name,
            "description": s.description,
            "domains": s.supported_domains,
            "comparison_types": s.comparison_types,
        }
        for s in SKILL_CATALOG.values()
    ]
