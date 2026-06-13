"""Skill catalog — extended registry with matching and scoring logic."""

from __future__ import annotations

import re
from typing import Any

from agent.skills import SKILL_CATALOG, SkillCapability, find_skill_for_query, list_skills


def score_skill_for_query(
    skill: SkillCapability,
    query: str,
    url: str = "",
) -> float:
    """Score how well a skill matches a query (0.0 to 1.0)."""
    query_lower = query.lower()
    score = 0.0

    comparison_keywords = [
        "compare", "comparison", "vs", "versus", "top", "best",
        "rank", "ranking", "sorted", "sort", "list",
    ]
    for kw in comparison_keywords:
        if kw in query_lower:
            score += 0.2

    # Score based on comparison types mentioned
    type_keywords = {
        "model": "ai_models",
        "ai": "ai_models",
        "llm": "ai_models",
        "product": "products",
        "tool": "saas",
        "saas": "saas",
        "software": "saas",
        "repo": "repositories",
        "repository": "repositories",
        "github": "repositories",
        "api": "apis",
        "course": "courses",
        "cloud": "cloud_services",
        "institute": "training_institutes",
        "training": "training_institutes",
    }
    for keyword, comp_type in type_keywords.items():
        if keyword in query_lower and comp_type in skill.comparison_types:
            score += 0.15

    # URL domain matching
    if url:
        for domain in skill.supported_domains:
            if domain in url.lower():
                score += 0.25

    # HuggingFace specific
    if "huggingface" in query_lower and "huggingface.co" in skill.supported_domains:
        score += 0.3

    return min(score, 1.0)


def select_best_skill(
    query: str,
    url: str = "",
) -> tuple[SkillCapability, float]:
    """Select the best skill for a query with confidence score."""
    best_skill = find_skill_for_query(query, url)
    if not best_skill:
        best_skill = SKILL_CATALOG.get("browser_comparison", SkillCapability(
            skill_name="browser_comparison",
            description="General browser comparison",
        ))

    confidence = score_skill_for_query(best_skill, query, url)
    return best_skill, confidence


def get_comparison_dimensions(query: str) -> list[str]:
    """Automatically determine comparison dimensions from query."""
    query_lower = query.lower()
    dimensions = []

    dimension_map = {
        "like": "likes",
        "download": "downloads",
        "price": "price",
        "cost": "price",
        "rating": "rating",
        "score": "score",
        "review": "reviews",
        "star": "rating",
        "popular": "popularity",
        "feature": "features",
        "description": "description",
        "name": "name",
    }

    for keyword, dim in dimension_map.items():
        if keyword in query_lower:
            if dim not in dimensions:
                dimensions.append(dim)

    if not dimensions:
        dimensions = ["name", "likes", "downloads", "rating"]

    return dimensions


def get_ranking_criteria(query: str) -> str:
    """Determine the primary ranking criteria from query."""
    query_lower = query.lower()
    criteria_map = {
        "like": "likes",
        "download": "downloads",
        "popular": "popularity",
        "rating": "rating",
        "review": "reviews",
        "price": "price",
        "cheapest": "price_asc",
        "most expensive": "price_desc",
        "top": "default",
        "best": "default",
        "new": "newest",
        "recent": "newest",
    }

    for keyword, criteria in criteria_map.items():
        if keyword in query_lower:
            return criteria

    return "likes"  # default ranking


def identify_site_from_query(query: str) -> str | None:
    """Identify target site from query."""
    query_lower = query.lower()

    site_map = {
        r"huggingface": "https://huggingface.co",
        r"github": "https://github.com",
        r"producthunt": "https://producthunt.com",
        r"amazon": "https://amazon.com",
        r"pypi": "https://pypi.org",
    }

    for pattern, url in site_map.items():
        if re.search(pattern, query_lower):
            return url

    return None


def get_visible_actions_required(skill: SkillCapability | None = None) -> int:
    """Get minimum visible browser actions required."""
    if skill:
        return skill.min_actions
    return 3


__all__ = [
    "score_skill_for_query",
    "select_best_skill",
    "get_comparison_dimensions",
    "get_ranking_criteria",
    "identify_site_from_query",
    "get_visible_actions_required",
]
