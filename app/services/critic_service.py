"""Critic service — verifies evidence support and triggers recovery."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

CRITIC_PROMPT = """You are a verification critic for a website intelligence system. Given a question, an answer, and the evidence used, evaluate:

1. SUPPORT: Does each claim in the answer have corresponding evidence?
2. COMPLETENESS: Does the answer fully address the question based on available evidence?
3. ACCURACY: Are there any contradictions between the answer and evidence?

Return JSON with: "status" ("passed"|"failed"|"partial"), "reasons" (list of issues found), "recovery_action" (what to do if failed)."""


async def verify_answer(
    question: str,
    answer: str,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify an answer against its evidence."""
    settings = get_settings()

    evidence_summary = "\n".join(
        [
            f"- URL: {e.get('source_url')} | Type: {e.get('artifact_type')} | Score: {e.get('score', 0):.2f}"
            for e in evidence[:10]
        ]
    )

    messages = [
        {"role": "system", "content": CRITIC_PROMPT},
        {
            "role": "user",
            "content": f"Question: {question}\n\nAnswer: {answer}\n\nEvidence:\n{evidence_summary}\n\nVerify this answer. Return JSON.",
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.1,
                    "max_tokens": 512,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)
    except Exception as exc:
        logger.warning("Critic verification failed: %s", exc)
        result = {
            "status": "failed",
            "reasons": [f"Critic service error: {exc}"],
            "recovery_action": "retry_with_more_evidence",
        }

    return result